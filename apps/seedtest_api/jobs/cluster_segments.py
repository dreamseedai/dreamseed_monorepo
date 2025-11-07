#!/usr/bin/env python3
"""
Clustering (tidymodels) - Learning Pattern Segments

Clusters users based on learning patterns:
- Features: A_t components, I_t/E_t/R_t distribution, response time, hint usage, frequency, gaps
- Method: k-means or Gaussian mixture (tidymodels)
- Output: segment labels (e.g., "short_frequent", "long_rare", "hint_heavy")

Stores:
- user_segment: user_id, segment_label, features_snapshot
- segment_meta: cluster centers, silhouette scores
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import sqlalchemy as sa

from ..app.clients.r_forecast import RForecastClient
from ..services.db import get_session


async def cluster_user_segments(
    lookback_weeks: int | None = None,
    n_clusters: int | None = None,
    method: str = "kmeans",
) -> None:
    """
    Cluster users into learning pattern segments.
    
    Args:
        lookback_weeks: Number of weeks to look back (default: 12)
        n_clusters: Number of clusters (default: 3)
        method: Clustering method ("kmeans", "hierarchical", "dbscan")
    """
    lookback_weeks = int(
        lookback_weeks
        if lookback_weeks is not None
        else os.getenv("CLUSTER_LOOKBACK_WEEKS", "12")
    )
    # Determine number of clusters robustly
    env_k = os.getenv("CLUSTER_N_CLUSTERS", "3")
    if env_k is None or env_k.strip() == "":
        env_k = "3"
    try:
        n_clusters = int(n_clusters) if n_clusters is not None else int(env_k)
    except Exception:
        n_clusters = 3
    method = os.getenv("CLUSTER_METHOD", method).lower()
    
    # Initialize R Forecast client (clustering endpoints included)
    try:
        client = RForecastClient()
    except RuntimeError as e:
        print(f"[ERROR] Failed to initialize R Forecast client: {e}")
        return
    
    print(f"[INFO] Clustering user segments (lookback={lookback_weeks} weeks)")
    
    # Load user features
    since_date = date.today() - timedelta(weeks=lookback_weeks)

    with get_session() as s:
        stmt = sa.text(
            """
            WITH user_agg AS (
                SELECT 
                    user_id,
                    AVG((kpis->>'A_t')::float) AS avg_engagement,
                    AVG((kpis->>'I_t')::float) AS avg_improvement,
                    AVG((kpis->>'E_t')::float) AS avg_efficiency,
                    AVG((kpis->>'R_t')::float) AS avg_recovery,
                    AVG((kpis->>'sessions')::int) AS avg_sessions,
                    AVG((kpis->>'mean_gap')::float) AS avg_gap
                FROM weekly_kpi
                WHERE week_start >= :since_date
                  AND kpis ? 'A_t'
                GROUP BY user_id
                HAVING COUNT(*) >= 4
            ),
            topic_agg AS (
                SELECT 
                    user_id,
                    AVG(rt_median) AS avg_rt,
                    AVG(hints) AS avg_hints,
                    SUM(attempts) AS total_attempts
                FROM features_topic_daily
                WHERE date >= :since_date
                GROUP BY user_id
            )
            SELECT 
                u.user_id,
                COALESCE(u.avg_engagement, 0) AS engagement,
                COALESCE(u.avg_improvement, 0) AS improvement,
                COALESCE(u.avg_efficiency, 0) AS efficiency,
                COALESCE(u.avg_recovery, 0) AS recovery,
                COALESCE(u.avg_sessions, 0) AS sessions,
                COALESCE(u.avg_gap, 7) AS gap,
                COALESCE(t.avg_rt, 30) AS avg_rt,
                COALESCE(t.avg_hints, 0) AS avg_hints,
                COALESCE(t.total_attempts, 0) AS total_attempts
            FROM user_agg u
            LEFT JOIN topic_agg t ON u.user_id = t.user_id
            """
        )
        
        rows = s.execute(stmt, {"since_date": since_date}).mappings().all()
        
        if not rows or len(rows) < 10:
            print("[WARN] Insufficient users for clustering (need >= 10)")
            return
        
        print(f"[INFO] Loaded {len(rows)} user feature vectors")
        
        data_rows = []
        for r in rows:
            data_rows.append({
                "user_id": str(r["user_id"]),
                "engagement": float(r["engagement"]),
                "improvement": float(r["improvement"]),
                "efficiency": float(r["efficiency"]),
                "recovery": float(r["recovery"]),
                "sessions": float(r["sessions"]),
                "gap": float(r["gap"]),
                "avg_rt": float(r["avg_rt"]),
                "avg_hints": float(r["avg_hints"]),
                "total_attempts": float(r["total_attempts"]),
            })
    
    # Call R Clustering service
    
    try:
        result = await client.cluster_fit(
            data_rows,
            method=method,
            k=n_clusters,
        )
        
        if result.get("error"):
            print(f"[WARN] Clustering fit returned error: {result.get('error')}")
            return
            
    except Exception as e:
        print(f"[ERROR] R Clustering service call failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Extract results (new API returns: {status, method, k, clusters: {user_id: cluster_id}, centers, ...})
    assignments = result.get("clusters") or {}
    centers = result.get("centers") or []
    actual_k = result.get("k", len(centers))
    metrics = {
        "withinss": result.get("withinss"),
        "tot_withinss": result.get("tot_withinss"),
        "betweenss": result.get("betweenss"),
    }
    
    print(f"[INFO] Clustered into {actual_k} segments")
    print(f"[INFO] Metrics: {metrics}")
    
    # Store results
    with get_session() as s:
        # Ensure tables exist
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS segment_meta (
                run_id TEXT PRIMARY KEY,
                method TEXT,
                n_clusters INT,
                centers JSONB,
                metrics JSONB,
                fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ))
        s.execute(sa.text(
            """
            CREATE TABLE IF NOT EXISTS user_segment (
                user_id TEXT PRIMARY KEY,
                segment_label TEXT,
                features_snapshot JSONB,
                assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ))
        # Store segment metadata
        stmt_meta = sa.text(
            """
            INSERT INTO segment_meta (
                run_id,
                method,
                n_clusters,
                centers,
                metrics,
                fitted_at
            )
            VALUES (
                :run_id,
                :method,
                :n_clusters,
                CAST(:centers::text AS jsonb),
                CAST(:metrics::text AS jsonb),
                NOW()
            )
            ON CONFLICT (run_id) DO UPDATE SET
                centers = EXCLUDED.centers,
                metrics = EXCLUDED.metrics,
                fitted_at = NOW()
            """
        )

        run_id = f"cluster-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        s.execute(
            stmt_meta,
            {
                "run_id": run_id,
                "method": method,
                "n_clusters": actual_k,
                "centers": json.dumps(centers),
                "metrics": json.dumps(metrics),
            },
        )
        
        # Store user segment assignments
        stmt_segment = sa.text(
            """
            INSERT INTO user_segment (
                user_id,
                segment_label,
                features_snapshot,
                assigned_at
            )
            VALUES (
                :user_id,
                :segment_label,
                CAST(:features_snapshot::text AS jsonb),
                NOW()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                segment_label = EXCLUDED.segment_label,
                features_snapshot = EXCLUDED.features_snapshot,
                assigned_at = NOW()
            """
        )
        
        # Helper function to generate meaningful segment labels
        def _generate_segment_label(
            cluster_id: int, user_features: Dict[str, Any], centers: List[Dict[str, Any]]
        ) -> str:
            """Generate meaningful segment label based on user features and cluster characteristics.
            
            Labels:
            - "short_frequent": 짧고 자주 (낮은 gap, 높은 sessions)
            - "long_rare": 길고 드물게 (높은 gap, 낮은 sessions)
            - "hint_heavy": 힌트 집중형 (높은 avg_hints)
            - "improving": 향상 지속형 (높은 improvement)
            - "struggling": 어려움 겪는형 (낮은 efficiency, 높은 hints)
            - "efficient": 효율적 (높은 efficiency, 낮은 hints)
            """
            gap = user_features.get("gap", 7.0)
            sessions = user_features.get("sessions", 0.0)
            hints = user_features.get("avg_hints", 0.0)
            improvement = user_features.get("improvement", 0.0)
            efficiency = user_features.get("efficiency", 0.0)
            
            # Rule-based labeling based on characteristic patterns
            if gap < 3.0 and sessions > 10.0:
                return "short_frequent"  # 짧고 자주
            elif gap > 7.0 and sessions < 5.0:
                return "long_rare"  # 길고 드물게
            elif hints > 2.0:
                return "hint_heavy"  # 힌트 집중형
            elif improvement > 0.3:
                return "improving"  # 향상 지속형
            elif efficiency < 0.4 and hints > 1.5:
                return "struggling"  # 어려움 겪는형
            elif efficiency > 0.7 and hints < 0.5:
                return "efficient"  # 효율적
            else:
                # Fallback to cluster ID if no clear pattern
                return f"cluster_{cluster_id}"
        
        for user_id, cluster_id in assignments.items():
            # Find features for this user
            user_features = next(
                (r for r in data_rows if r["user_id"] == user_id),
                {}
            )
            
            # Generate meaningful segment label
            segment_label = _generate_segment_label(cluster_id, user_features, centers)
            
            s.execute(
                stmt_segment,
                {
                    "user_id": user_id,
                    "segment_label": segment_label,
                    "features_snapshot": json.dumps(user_features),
                },
            )
        
        s.commit()
    
    print(f"[INFO] Clustering completed: run_id={run_id}, {len(assignments)} users assigned")


async def main() -> None:
    await cluster_user_segments()


if __name__ == "__main__":
    asyncio.run(main())
