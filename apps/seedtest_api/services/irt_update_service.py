"""IRT 온라인 능력 업데이트 서비스

세션 종료 시 최근 시도 데이터를 기반으로 EAP (Expected A Posteriori) 또는
Maximum Likelihood 추정을 수행하여 사용자의 능력(θ)을 실시간으로 업데이트합니다.
"""
# cSpell:ignore mirt
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..app.clients.r_irt import RIrtClient
from ..services.db import get_session

logger = logging.getLogger(__name__)


def load_recent_attempts(
    session: Session,
    user_id: str,
    lookback_days: int = 30,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Load recent attempts from attempt VIEW or exam_results.
    
    Args:
        session: Database session
        user_id: User identifier
        lookback_days: Number of days to look back
        limit: Maximum number of attempts to return
    
    Returns:
        List of attempts with item_id, is_correct, responded_at
    """
    since_dt = datetime.utcnow() - timedelta(days=lookback_days)
    observations: List[Dict[str, Any]] = []
    
    # Try attempt VIEW first
    stmt = sa.text(
        """
        SELECT 
            item_id::text AS item_id,
            correct AS is_correct,
            completed_at AS responded_at
        FROM attempt
        WHERE student_id::text = :user_id
          AND completed_at >= :since
          AND item_id IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT :limit
        """
    )
    
    try:
        rows = session.execute(
            stmt, {"user_id": user_id, "since": since_dt, "limit": limit}
        ).mappings().all()
        for r in rows:
            observations.append({
                "item_id": str(r["item_id"]),
                "is_correct": bool(r["is_correct"]) if r["is_correct"] is not None else False,
                "responded_at": str(r["responded_at"]),
            })
    except Exception:
        # Fallback to exam_results if attempt VIEW not available
        stmt2 = sa.text(
            """
            SELECT result_json
            FROM exam_results
            WHERE user_id = :user_id
              AND COALESCE(updated_at, created_at) >= :since
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT :limit
            """
        )
        try:
            rows = session.execute(
                stmt2, {"user_id": user_id, "since": since_dt, "limit": limit}
            ).mappings().all()
            for r in rows:
                doc = r.get("result_json") or {}
                for q in doc.get("questions") or []:
                    iid = q.get("question_id")
                    if iid is None:
                        continue
                    is_corr = q.get("is_correct")
                    if is_corr is None:
                        is_corr = q.get("correct")
                    observations.append({
                        "item_id": str(iid),
                        "is_correct": bool(is_corr) if is_corr is not None else False,
                        "responded_at": str(doc.get("created_at") or datetime.utcnow().isoformat()),
                    })
        except Exception:
            pass
    
    return observations


def load_item_params(
    session: Session,
    item_ids: List[str],
    model: str = "2PL",
    version: str = "v1",
) -> Dict[str, Dict[str, Any]]:
    """Load IRT item parameters from mirt_item_params or question.meta.
    
    Args:
        session: Database session
        item_ids: List of item IDs
        model: IRT model type (2PL, 3PL)
        version: Parameter version
    
    Returns:
        Dictionary mapping item_id to parameters (a, b, c)
    """
    params_map: Dict[str, Dict[str, Any]] = {}
    
    if not item_ids:
        return params_map
    
    # Try mirt_item_params first
    stmt = sa.text(
        """
        SELECT item_id, params
        FROM mirt_item_params
        WHERE item_id = ANY(:item_ids)
          AND model = :model
          AND version = :version
        """
    )
    
    try:
        rows = session.execute(
            stmt, {"item_ids": item_ids, "model": model, "version": version}
        ).mappings().all()
        for r in rows:
            item_id = str(r["item_id"])
            params = r.get("params") or {}
            if isinstance(params, str):
                import json
                params = json.loads(params)
            params_map[item_id] = params
    except Exception:
        pass
    
    # Fallback: Load from question.meta JSONB
    if len(params_map) < len(item_ids):
        missing_ids = [iid for iid in item_ids if iid not in params_map]
        stmt2 = sa.text(
            """
            SELECT id::text AS item_id, meta
            FROM question
            WHERE id = ANY(:item_ids)
              AND meta IS NOT NULL
              AND meta ? 'irt'
            """
        )
        try:
            rows = session.execute(
                stmt2, {"item_ids": missing_ids}
            ).mappings().all()
            for r in rows:
                item_id = str(r["item_id"])
                meta = r.get("meta") or {}
                if isinstance(meta, str):
                    import json
                    meta = json.loads(meta)
                irt = meta.get("irt", {})
                if irt:
                    params_map[item_id] = {
                        "a": irt.get("a", 1.0),
                        "b": irt.get("b", 0.0),
                        "c": irt.get("c", 0.2 if model == "3PL" else 0.0),
                    }
        except Exception:
            pass
    
    return params_map


async def update_ability_async(
    user_id: str,
    session_id: Optional[str] = None,
    lookback_days: int = 30,
    model: str = "2PL",
    version: str = "v1",
) -> Optional[Tuple[float, float]]:
    """Update user ability (θ) asynchronously using EAP/MI estimation.
    
    Args:
        user_id: User identifier
        session_id: Session ID (optional, for logging)
        lookback_days: Number of days to look back for attempts
        model: IRT model type
        version: Parameter version
    
    Returns:
        Tuple of (theta, standard_error) or None if update failed
    """
    try:
        with get_session() as db_session:
            # Load recent attempts
            attempts = load_recent_attempts(db_session, user_id, lookback_days)
            if not attempts:
                return None
            
            # Extract unique item IDs
            item_ids = list(set(a["item_id"] for a in attempts))
            
            # Load item parameters
            item_params_map = load_item_params(db_session, item_ids, model, version)
            
            if not item_params_map:
                # No item parameters available
                return None
            
            # Filter attempts to only include items with known parameters
            valid_attempts = [
                a for a in attempts
                if a["item_id"] in item_params_map
            ]
            
            if not valid_attempts:
                return None
            
            # Prepare item_params and responses for R IRT service
            # RIrtClient.score expects: item_params as Dict[str, Dict] (item_id -> params)
            # and responses as List[Dict] (list of response dicts)
            item_params_dict = {}
            responses_list = []
            
            for a in valid_attempts:
                item_id = a["item_id"]
                params = item_params_map[item_id]
                # Store params in dict keyed by item_id
                item_params_dict[item_id] = {
                    "a": params.get("a", 1.0),
                    "b": params.get("b", 0.0),
                    "c": params.get("c", 0.2 if model == "3PL" else 0.0),
                }
                responses_list.append({
                    "item_id": item_id,
                    "is_correct": a["is_correct"],
                })
            
            # Call R IRT service for EAP estimation
            # Default to internal service URL if not set
            base_url = os.getenv("R_IRT_BASE_URL") or "http://r-irt-plumber.seedtest.svc.cluster.local:80"
            
            logger.info(
                f"Calling R IRT service for user={user_id} session={session_id} "
                f"with {len(item_params_dict)} items",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "item_count": len(item_params_dict),
                    "base_url": base_url,
                },
            )
            
            try:
                client = RIrtClient(base_url=base_url)
                result = await client.score(item_params_dict, responses_list)
                
                logger.info(
                    f"R IRT service returned theta={result.get('theta')} for user={user_id}",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "theta": result.get("theta"),
                        "se": result.get("standard_error") or result.get("se"),
                    },
                )
            except Exception as e:
                logger.error(
                    f"R IRT service call failed for user={user_id} session={session_id}: {e}",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "error": str(e),
                        "base_url": base_url,
                    },
                    exc_info=True,
                )
                return None
            
            # Extract theta and standard error
            theta = result.get("theta")
            se = result.get("standard_error") or result.get("se")
            
            if theta is None:
                logger.warning(
                    f"R IRT service returned None theta for user={user_id} session={session_id}",
                    extra={"user_id": user_id, "session_id": session_id},
                )
                return None
            
            # Update mirt_ability table
            stmt = sa.text(
                """
                INSERT INTO mirt_ability (user_id, theta, se, model, version, fitted_at)
                VALUES (:user_id, :theta, :se, :model, :version, NOW())
                ON CONFLICT (user_id, version)
                DO UPDATE SET
                    theta = EXCLUDED.theta,
                    se = EXCLUDED.se,
                    model = EXCLUDED.model,
                    fitted_at = NOW()
                """
            )
            
            db_session.execute(
                stmt,
                {
                    "user_id": user_id,
                    "theta": float(theta),
                    "se": float(se) if se is not None else None,
                    "model": model,
                    "version": version,
                },
            )
            db_session.commit()
            
            logger.info(
                f"Successfully updated ability for user={user_id}: theta={theta} se={se}",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "theta": float(theta),
                    "se": float(se) if se is not None else 0.0,
                    "model": model,
                    "version": version,
                },
            )
            
            return (float(theta), float(se) if se is not None else 0.0)
    
    except Exception as e:
        # Log error but don't fail the session completion
        logger.error(
            f"Failed to update ability for user={user_id} session={session_id}: {e}",
            extra={"user_id": user_id, "session_id": session_id, "error": str(e)},
            exc_info=True,
        )
        return None


def update_ability_sync(
    user_id: str,
    session_id: Optional[str] = None,
    lookback_days: int = 30,
    model: str = "2PL",
    version: str = "v1",
) -> Optional[Tuple[float, float]]:
    """Synchronous wrapper for update_ability_async.
    
    Args:
        user_id: User identifier
        session_id: Session ID (optional)
        lookback_days: Number of days to look back
        model: IRT model type
        version: Parameter version
    
    Returns:
        Tuple of (theta, standard_error) or None
    """
    try:
        return asyncio.run(
            update_ability_async(user_id, session_id, lookback_days, model, version)
        )
    except Exception as e:
        print(f"[WARN] Failed to run async ability update: {e}")
        return None


def trigger_ability_update(
    user_id: str,
    session_id: Optional[str] = None,
    background: bool = True,
) -> None:
    """Trigger ability update (non-blocking if background=True).
    
    Args:
        user_id: User identifier
        session_id: Session ID (optional)
        background: If True, run in background without blocking
    """
    if background:
        # Run in background thread/event loop
        try:
            import threading
            thread = threading.Thread(
                target=lambda: update_ability_sync(user_id, session_id),
                daemon=True,
            )
            thread.start()
        except Exception:
            # Fallback: try asyncio if threading fails
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        update_ability_async(user_id, session_id)
                    )
                else:
                    loop.run_until_complete(
                        update_ability_async(user_id, session_id)
                    )
            except Exception as e:
                logger.error(
                    f"Failed to trigger background ability update: {e}",
                    extra={"user_id": user_id, "session_id": session_id, "error": str(e)},
                    exc_info=True,
                )
    else:
        # Blocking call
        update_ability_sync(user_id, session_id)

