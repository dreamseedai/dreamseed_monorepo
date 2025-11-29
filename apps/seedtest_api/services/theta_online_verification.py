"""θ 온라인 업데이트 검증 유틸리티

세션 완료 후 능력 업데이트가 정상 작동하는지 확인하는 도구.
"""

from __future__ import annotations

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

from datetime import datetime, timedelta
from sqlalchemy import text
from apps.seedtest_api.services.db import get_session


def check_recent_ability_updates(hours: int = 24) -> list[dict]:
    """최근 N시간 내 능력 업데이트 확인.

    Args:
        hours: 확인할 시간 범위

    Returns:
        최근 업데이트된 사용자 목록
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    with get_session() as session:
        result = session.execute(
            text(
                """
                SELECT 
                    user_id,
                    theta,
                    se,
                    model,
                    version,
                    fitted_at
                FROM mirt_ability
                WHERE fitted_at >= :since
                ORDER BY fitted_at DESC
                LIMIT 50
            """
            ),
            {"since": since},
        )
        rows = result.fetchall()

        return [
            {
                "user_id": row[0],
                "theta": float(row[1]) if row[1] else None,
                "se": float(row[2]) if row[2] else None,
                "model": row[3],
                "version": row[4],
                "fitted_at": row[5].isoformat() if row[5] else None,
            }
            for row in rows
        ]


def check_session_completions(hours: int = 24) -> list[dict]:
    """최근 N시간 내 세션 완료 확인.

    Args:
        hours: 확인할 시간 범위

    Returns:
        최근 완료된 세션 목록
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    with get_session() as session:
        # exam_results에서 완료된 세션 확인
        result = session.execute(
            text(
                """
                SELECT 
                    session_id,
                    user_id,
                    COALESCE(updated_at, created_at) AS completed_at
                FROM exam_results
                WHERE COALESCE(updated_at, created_at) >= :since
                ORDER BY COALESCE(updated_at, created_at) DESC
                LIMIT 50
            """
            ),
            {"since": since},
        )
        rows = result.fetchall()

        return [
            {
                "session_id": row[0],
                "user_id": row[1],
                "completed_at": row[2].isoformat() if row[2] else None,
            }
            for row in rows
        ]


def verify_theta_update_for_user(user_id: str) -> dict:
    """특정 사용자의 능력 업데이트 검증.

    Args:
        user_id: 사용자 ID

    Returns:
        검증 결과
    """
    with get_session() as session:
        # 최근 업데이트 확인
        result = session.execute(
            text(
                """
                SELECT theta, se, fitted_at
                FROM mirt_ability
                WHERE user_id = :user_id
                ORDER BY fitted_at DESC
                LIMIT 1
            """
            ),
            {"user_id": user_id},
        )
        row = result.fetchone()

        # 최근 시도 확인
        result2 = session.execute(
            text(
                """
                SELECT COUNT(*), MAX(completed_at)
                FROM attempt
                WHERE student_id::text = :user_id
                  AND completed_at >= NOW() - INTERVAL '7 days'
            """
            ),
            {"user_id": user_id},
        )
        row2 = result2.fetchone()

        return {
            "user_id": user_id,
            "latest_theta": float(row[0]) if row and row[0] else None,
            "latest_se": float(row[1]) if row and row[1] else None,
            "theta_updated_at": row[2].isoformat() if row and row[2] else None,
            "recent_attempts_7d": row2[0] if row2 else 0,
            "latest_attempt_at": row2[1].isoformat() if row2 and row2[1] else None,
        }


def main() -> None:
    """CLI 진입점."""
    import argparse

    parser = argparse.ArgumentParser(description="θ 온라인 업데이트 검증")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="확인할 시간 범위 (기본 24시간)",
    )
    parser.add_argument(
        "--user-id",
        help="특정 사용자 검증",
    )

    args = parser.parse_args()

    if args.user_id:
        result = verify_theta_update_for_user(args.user_id)
        print(f"User: {result['user_id']}")
        print(f"Latest theta: {result['latest_theta']}")
        print(f"Latest SE: {result['latest_se']}")
        print(f"Theta updated at: {result['theta_updated_at']}")
        print(f"Recent attempts (7d): {result['recent_attempts_7d']}")
        print(f"Latest attempt: {result['latest_attempt_at']}")
    else:
        print(f"=== 최근 {args.hours}시간 내 능력 업데이트 ===")
        updates = check_recent_ability_updates(args.hours)
        print(f"총 {len(updates)}건의 업데이트")
        for u in updates[:10]:
            print(
                f"  {u['user_id']}: θ={u['theta']:.3f}, se={u['se']:.3f}, at={u['fitted_at']}"
            )

        print(f"\n=== 최근 {args.hours}시간 내 세션 완료 ===")
        completions = check_session_completions(args.hours)
        print(f"총 {len(completions)}건의 세션 완료")
        for c in completions[:10]:
            print(f"  {c['session_id']}: user={c['user_id']}, at={c['completed_at']}")


if __name__ == "__main__":
    main()
