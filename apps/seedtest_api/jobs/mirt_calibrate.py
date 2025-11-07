#!/usr/bin/env python3
# cSpell:ignore mirt lookback CALIB
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import sqlalchemy as sa

from ..app.clients.r_irt import RIrtClient

# Reuse app DB utilities
from ..services.db import get_session


async def run_calibration(
    lookback_days: int | None = None,
    model: str | None = None,
    topic_id: str | None = None,
    subject_id: int | None = None,
) -> None:
    # Env compatibility: prefer MIRT_* names, fall back to legacy IRT_* names
    lookback_val = (
        str(lookback_days)
        if lookback_days is not None
        else os.getenv("MIRT_LOOKBACK_DAYS")
        or os.getenv("IRT_CALIB_LOOKBACK_DAYS")
        or "30"
    )
    lookback_days = int(lookback_val)
    model = (
        (model or os.getenv("MIRT_MODEL") or os.getenv("IRT_MODEL") or "2PL")
        .strip()
    )
    # Optional topic_id/subject_id filter for topic/subject-specific calibration banks
    topic_id = topic_id or os.getenv("MIRT_TOPIC_ID") or os.getenv("IRT_TOPIC_ID")
    if subject_id is None:
        subject_id_env = os.getenv("MIRT_SUBJECT_ID") or os.getenv("IRT_SUBJECT_ID")
        if subject_id_env:
            try:
                subject_id = int(subject_id_env)
            except Exception:
                subject_id = None
    # Optional maximum observations cap (0 or missing = unlimited)
    try:
        max_obs = int(os.getenv("MIRT_MAX_OBS", "0") or "0")
    except Exception:
        max_obs = 0
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    observations: List[Dict[str, Any]] = []
    anchors: List[Dict[str, Any]] = []

    # Extract observations (user_id, item_id, is_correct, responded_at)
    # Priority order: attempt VIEW > responses table > exam_results JSON
    since_dt = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    
    with get_session() as s:
        # Try attempt VIEW first (standardized schema)
        # Apply topic_id/subject_id filtering if specified (for topic/subject-specific calibration banks)
        limit_clause = f"LIMIT {max_obs}" if max_obs > 0 else ""
        
        # Build WHERE clause with optional topic/subject filters
        where_clauses = [
            "completed_at >= :since",
            "item_id IS NOT NULL",
            "student_id IS NOT NULL",
        ]
        params: Dict[str, Any] = {"since": since_dt}
        
        if topic_id:
            # Filter by topic_id from attempt VIEW or question table
            where_clauses.append("(topic_id = :topic_id OR EXISTS (SELECT 1 FROM question q WHERE q.id = attempt.item_id AND q.topic_id = :topic_id))")
            params["topic_id"] = topic_id
            print(f"[INFO] Filtering by topic_id={topic_id} (topic-specific calibration bank)")
        
        if subject_id is not None:
            # Filter by exam_id (assuming exam_id maps to subject_id)
            # Note: This requires exam_results.exam_id to be available in attempt VIEW or join
            where_clauses.append("EXISTS (SELECT 1 FROM exam_results er WHERE er.session_id = attempt.session_id AND er.exam_id = :subject_id)")
            params["subject_id"] = subject_id
            print(f"[INFO] Filtering by subject_id={subject_id} (subject-specific calibration bank)")
        
        where_clause = " AND ".join(where_clauses)
        
        stmt_attempt = sa.text(
            f"""
            SELECT 
                student_id::text AS user_id,
                item_id::text AS item_id,
                correct AS is_correct,
                completed_at AS responded_at
            FROM attempt
            WHERE {where_clause}
            ORDER BY completed_at
            {limit_clause}
            """
        )
        
        # Fallback 1: responses table
        stmt_responses = sa.text(
            """
            SELECT user_id, item_id, is_correct, responded_at
            FROM responses
            WHERE responded_at >= :since
            ORDER BY responded_at
            LIMIT 10000
            """
        )
        
        # Fallback 2: exam_results JSON
        stmt_exam_results = sa.text(
            """
            SELECT user_id, session_id, COALESCE(updated_at, created_at) AS ts, result_json
            FROM exam_results
            WHERE COALESCE(updated_at, created_at) >= :since
            ORDER BY COALESCE(updated_at, created_at)
            LIMIT 10000
            """
        )
        
    # Try attempt VIEW
        try:
            rows = s.execute(stmt_attempt, {"since": since_dt}).mappings().all()
            for r in rows:
                observations.append(
                    {
                        "user_id": str(r["user_id"]),
                        "item_id": str(r["item_id"]),
                        "is_correct": bool(r["is_correct"]) if r["is_correct"] is not None else False,
                        "responded_at": str(r["responded_at"]),
                    }
                )
            if observations:
                print(f"[INFO] Loaded {len(observations)} observations from attempt VIEW")
        except Exception as e:
            print(f"[WARN] attempt VIEW not available: {e}; trying fallback...")
            try:
                s.rollback()
            except Exception:
                pass
            
            # Fallback 1: responses table
            try:
                rows = s.execute(stmt_responses, {"since": since_dt}).mappings().all()
                for r in rows:
                    observations.append(
                        {
                            "user_id": str(r["user_id"]),
                            "item_id": str(r["item_id"]),
                            "is_correct": bool(r["is_correct"]),
                            "responded_at": str(r["responded_at"]),
                        }
                    )
                if observations:
                    print(f"[INFO] Loaded {len(observations)} observations from responses table")
            except Exception as e2:
                print(f"[WARN] responses table not available: {e2}; trying exam_results...")
                try:
                    s.rollback()
                except Exception:
                    pass
                
                # Fallback 2: exam_results JSON
                try:
                    rows = s.execute(stmt_exam_results, {"since": since_dt}).mappings().all()
                    for r in rows:
                        doc = r.get("result_json") or {}
                        for q in doc.get("questions") or []:
                            iid = q.get("question_id")
                            if iid is None:
                                continue
                            is_corr = q.get("is_correct")
                            if is_corr is None:
                                is_corr = q.get("correct")
                            observations.append(
                                {
                                    "user_id": str(r.get("user_id") or ""),
                                    "item_id": str(iid),
                                    "is_correct": (
                                        bool(is_corr) if is_corr is not None else False
                                    ),
                                    "responded_at": str(r.get("ts")),
                                }
                            )
                    if observations:
                        print(f"[INFO] Loaded {len(observations)} observations from exam_results JSON")
                except Exception as e3:
                    print(f"[ERROR] All data sources failed. Last error: {e3}")

        # Load anchors from question.meta (irt seeds and anchor tags) if available
        try:
            stmt_anchors = sa.text(
                """
                SELECT 
                  id::text AS item_id,
                  meta->'irt' AS irt,
                  EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(meta->'tags') t
                    WHERE t = 'anchor'
                  ) AS is_anchor
                FROM question
                WHERE (meta ? 'irt') OR (
                  meta ? 'tags' AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(meta->'tags') t
                    WHERE t = 'anchor'
                  )
                )
                LIMIT 10000
                """
            )
            rows = s.execute(stmt_anchors).mappings().all()
            for r in rows:
                params = {}
                irt_meta = r.get("irt") or {}
                # Extract a/b/c/model if present and numeric
                for k in ("a", "b", "c"):
                    v = irt_meta.get(k) if isinstance(irt_meta, dict) else None
                    try:
                        if v is not None:
                            params[k] = float(v)
                    except Exception:
                        pass
                mdl = None
                try:
                    mdl = irt_meta.get("model") if isinstance(irt_meta, dict) else None
                except Exception:
                    mdl = None
                if mdl:
                    params["model"] = str(mdl)
                entry = {
                    "item_id": str(r.get("item_id")),
                    "params": params,
                    "fixed": bool(r.get("is_anchor")),
                }
                # Don't include empty params unless fixed anchor
                if entry["fixed"] or entry["params"]:
                    anchors.append(entry)
            if anchors:
                print(f"[INFO] Loaded {len(anchors)} anchors/seeds from question.meta")
        except Exception as e:
            print(f"[WARN] question.meta not available for anchors: {e}")

    # Apply max observations cap, keeping most recent if needed
    if max_obs and len(observations) > max_obs:
        observations = observations[-max_obs:]

    if not observations:
        print("No observations found; exiting.")
        return

    print(f"[INFO] Total observations: {len(observations)}")
    print(f"[INFO] Model: {model}, Anchors: {len(anchors)}")
    
    if dry_run:
        print("[DRY_RUN] Skipping R IRT service call and DB updates")
        print(f"[DRY_RUN] Would calibrate {len(observations)} observations with {len(anchors)} anchors")
        return

    # Call R IRT service with retry logic
    client = RIrtClient()
    max_retries = int(os.getenv("MIRT_MAX_RETRIES", "3"))
    retry_delay = float(os.getenv("MIRT_RETRY_DELAY_SECS", "5.0"))
    
    result = None
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await client.calibrate(observations, model=model, anchors=(anchors or None))
            break  # Success
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                print(f"[WARN] R IRT service call failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"[INFO] Retrying in {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print(f"[ERROR] R IRT service call failed after {max_retries} attempts: {e}")
                raise
    
    if result is None:
        raise RuntimeError(f"Failed to calibrate after {max_retries} attempts: {last_error}")

    # Expected result contains item_params, abilities, and fit metadata
    items = result.get("item_params") or []
    abilities = result.get("abilities") or []
    meta = result.get("fit_meta") or {}
    
    # Extract linking constants if anchor equating was performed
    linking_constants = meta.get("linking_constants") or {}
    if linking_constants:
        print(f"[INFO] Linking constants received: {list(linking_constants.keys())}")

    up_item = sa.text(
        """
        INSERT INTO mirt_item_params (item_id, model, params, version, fitted_at)
        VALUES (:item_id, :model, CAST(:params::text AS jsonb), COALESCE(:version,'v1'), NOW())
        ON CONFLICT (item_id) DO UPDATE SET params=EXCLUDED.params, model=EXCLUDED.model, version=EXCLUDED.version, fitted_at=NOW()
        """
    )
    up_ability = sa.text(
        """
        INSERT INTO mirt_ability (user_id, theta, se, model, version, fitted_at)
        VALUES (:user_id, :theta, :se, :model, COALESCE(:version,'v1'), NOW())
        ON CONFLICT (user_id, version) DO UPDATE SET theta=EXCLUDED.theta, se=EXCLUDED.se, model=EXCLUDED.model, fitted_at=NOW()
        """
    )
    up_meta = sa.text(
        """
        INSERT INTO mirt_fit_meta (run_id, model_spec, metrics, fitted_at)
        VALUES (:run_id, CAST(:model_spec::text AS jsonb), CAST(:metrics::text AS jsonb), NOW())
        ON CONFLICT (run_id) DO UPDATE SET model_spec=EXCLUDED.model_spec, metrics=EXCLUDED.metrics, fitted_at=NOW()
        """
    )
    
    # Update question.meta.irt with finalized parameters (if enabled)
    update_question_meta = os.getenv("IRT_UPDATE_QUESTION_META", "false").lower() == "true"
    up_question_meta = sa.text(
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
    ) if update_question_meta else None

    with get_session() as s:
        item_count = 0
        for it in items:
            item_id_str = str(it.get("item_id"))
            item_params = it.get("params") or {}
            item_model = str(it.get("model") or model)
            item_version = str(it.get("version") or "v1")
            
            s.execute(
                up_item,
                {
                    "item_id": item_id_str,
                    "model": item_model,
                    "params": json.dumps(item_params),
                    "version": item_version,
                },
            )
            
            # Optionally update question.meta.irt with finalized parameters
            if update_question_meta and (up_question_meta is not None):
                try:
                    question_id_int = int(item_id_str)
                    irt_meta = {
                        "a": item_params.get("a"),
                        "b": item_params.get("b"),
                        "c": item_params.get("c"),
                        "model": item_model,
                        "version": item_version,
                    }
                    # Remove None values
                    irt_meta = {k: v for k, v in irt_meta.items() if v is not None}
                    
                    s.execute(
                        up_question_meta,
                        {
                            "question_id": question_id_int,
                            "irt_json": json.dumps(irt_meta),
                        },
                    )
                except (ValueError, Exception) as e:
                    # Skip if question_id is not numeric or question doesn't exist
                    print(f"[WARN] Failed to update question.meta for item_id={item_id_str}: {e}")
            
            item_count += 1
        
        ability_count = 0
        for ab in abilities:
            s.execute(
                up_ability,
                {
                    "user_id": str(ab.get("user_id")),
                    "theta": float(ab.get("theta") or 0.0),
                    "se": float(ab.get("se") or 0.0),
                    "model": str(ab.get("model") or model),
                    "version": str(ab.get("version") or "v1"),
                },
            )
            ability_count += 1
        
        # Store fit metadata including linking constants
        run_id = (
            meta.get("run_id") or f"fit-{datetime.now(tz=timezone.utc).isoformat()}"
        )
        model_spec = meta.get("model_spec") or {}
        metrics = meta.get("metrics") or {}
        
        # Include linking constants in model_spec if available
        if linking_constants:
            model_spec["linking_constants"] = linking_constants
        
        s.execute(
            up_meta,
            {
                "run_id": str(run_id),
                "model_spec": json.dumps(model_spec),
                "metrics": json.dumps(metrics),
            },
        )
        
        s.commit()

    print(f"Calibration upsert completed: {item_count} items, {ability_count} abilities")
    if linking_constants:
        print("Linking constants stored in fit_meta.model_spec.linking_constants")
    if update_question_meta:
        print(f"question.meta.irt updated for {item_count} items")


async def main(
    lookback_days: int | None = None,
    model: str | None = None,
    topic_id: str | None = None,
    subject_id: int | None = None,
    dry_run: bool = False,
) -> int:
    """
    Main entry point for IRT calibration.
    
    Returns:
        Exit code: 0 on success, 1 on failure
    """
    if dry_run:
        print("[INFO] DRY RUN MODE: No changes will be committed")
    
    try:
        await run_calibration(
            lookback_days=lookback_days,
            model=model,
            topic_id=topic_id,
            subject_id=subject_id,
        )
        return 0
    except Exception as e:
        print(f"[FATAL] IRT calibration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run IRT calibration (mirt/ltm/eRm) with optional topic/subject filtering"
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Number of days to look back (default: from MIRT_LOOKBACK_DAYS env)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="IRT model type (2PL, 3PL, Rasch; default: from MIRT_MODEL env or 2PL)",
    )
    parser.add_argument(
        "--topic-id",
        type=str,
        default=None,
        help="Filter by topic_id for topic-specific calibration bank (default: from MIRT_TOPIC_ID env)",
    )
    parser.add_argument(
        "--subject-id",
        type=int,
        default=None,
        help="Filter by subject_id (exam_id) for subject-specific calibration bank (default: from MIRT_SUBJECT_ID env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no database commits)",
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(
        main(
            lookback_days=args.lookback_days,
            model=args.model,
            topic_id=args.topic_id,
            subject_id=args.subject_id,
            dry_run=args.dry_run,
        )
    )
    exit(exit_code)


if __name__ == "__main__":
    cli()
