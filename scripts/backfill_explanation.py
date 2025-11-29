#!/usr/bin/env python3
"""
Backfill explanation from MySQL tbl_question.que_en_solution to PostgreSQL problems.mysql_metadata->>'explanation'

Usage:
    # Dry-run (default) - shows what would be updated
    python scripts/backfill_explanation.py

    # Actually perform the update
    python scripts/backfill_explanation.py --execute

    # Limit to specific number of records
    python scripts/backfill_explanation.py --limit 100

    # Execute with limit
    python scripts/backfill_explanation.py --execute --limit 1000
"""

import argparse
import sys
from typing import List, Tuple, Optional, Dict, Any, cast
import importlib.util
import psycopg
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime

# Database configurations
POSTGRES_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "dreamseed",
    "user": "postgres",
    "password": "DreamSeedAi0908",
}

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "mpcstudy_db",
    "user": "mpcstudy_root",
    "password": "2B3Z45J3DACT",
}


def get_mysql_connection():
    """Connect to MySQL database"""
    # Use unix_socket if localhost, otherwise use host
    conn_params = {
        "user": MYSQL_CONFIG["user"],
        "password": MYSQL_CONFIG["password"],
        "database": MYSQL_CONFIG["database"],
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
    }

    # Try to find MySQL socket
    import os

    possible_sockets = [
        "/var/run/mysqld/mysqld.sock",
        "/tmp/mysql.sock",
        "/var/lib/mysql/mysql.sock",
    ]

    mysql_socket = None
    for sock in possible_sockets:
        if os.path.exists(sock):
            mysql_socket = sock
            break

    if mysql_socket:
        conn_params["unix_socket"] = mysql_socket
    else:
        conn_params["host"] = MYSQL_CONFIG["host"]
        conn_params["port"] = MYSQL_CONFIG["port"]

    return pymysql.connect(**conn_params)


def get_postgres_connection():
    """Connect to PostgreSQL database"""
    return psycopg.connect(
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
    )


def find_candidates(limit: Optional[int] = None) -> List[Tuple[int, str, str]]:
    """
    Find records that need backfilling:
    - PostgreSQL explanation is empty or null
    - MySQL que_en_solution is not empty

    Returns:
        List of tuples: (mysql_id, current_explanation, que_en_solution)
    """
    print("=" * 80)
    print("STEP 1: Finding candidates for backfill...")
    print("=" * 80)

    mysql_conn = get_mysql_connection()
    pg_conn = get_postgres_connection()

    try:
        # Get MySQL data
        print("\n[MySQL] Fetching que_en_solution from tbl_question...")
        with mysql_conn.cursor() as cursor:
            sql = """
                SELECT 
                    que_id,
                    que_en_solution
                FROM tbl_question
                WHERE que_en_solution IS NOT NULL 
                  AND TRIM(que_en_solution) != ''
                  AND que_en_solution != '<p></p>'
                  AND que_en_solution != '<p><br /></p>'
            """
            if limit:
                sql += f" LIMIT {limit * 2}"  # Get more from MySQL since we'll filter in PG

            cursor.execute(sql)
            rows = cast(List[Dict[str, Any]], cursor.fetchall())
            mysql_data = {row["que_id"]: row["que_en_solution"] for row in rows}

        print(f"Found {len(mysql_data)} MySQL records with non-empty que_en_solution")

        # Get PostgreSQL data
        print("\n[PostgreSQL] Checking explanation status in problems table...")
        with pg_conn.cursor() as cursor:
            if limit:
                cursor.execute(
                    """
                    SELECT 
                        (mysql_metadata->>'mysql_id')::int as mysql_id,
                        COALESCE(mysql_metadata->>'explanation', '') as explanation
                    FROM problems
                    WHERE mysql_metadata ? 'mysql_id'
                    LIMIT %s
                    """,
                    (limit * 2,),
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        (mysql_metadata->>'mysql_id')::int as mysql_id,
                        COALESCE(mysql_metadata->>'explanation', '') as explanation
                    FROM problems
                    WHERE mysql_metadata ? 'mysql_id'
                    """,
                )

            pg_data = cursor.fetchall()

        print(f"Checked {len(pg_data)} PostgreSQL records")

        # Find matches
        candidates = []
        for row in pg_data:
            mysql_id = row[0]
            current_explanation = row[1]

            # Skip if explanation already exists
            if (
                current_explanation
                and current_explanation.strip()
                and current_explanation not in ["<p></p>", "<p><br /></p>"]
            ):
                continue

            # Check if MySQL has solution
            if mysql_id in mysql_data:
                que_en_solution = mysql_data[mysql_id]
                candidates.append((mysql_id, current_explanation, que_en_solution))

        if limit and len(candidates) > limit:
            candidates = candidates[:limit]

        return candidates

    finally:
        mysql_conn.close()
        pg_conn.close()


def preview_changes(candidates: List[Tuple[int, str, str]], preview_limit: int = 5):
    """Preview some of the changes that will be made"""
    print("\n" + "=" * 80)
    print(
        f"STEP 2: Preview of changes (showing first {preview_limit} of {len(candidates)} total)"
    )
    print("=" * 80)

    for i, (mysql_id, current_explanation, que_en_solution) in enumerate(
        candidates[:preview_limit], 1
    ):
        print(f"\n--- Record {i} (mysql_id: {mysql_id}) ---")
        print(
            f"Current explanation: '{current_explanation[:100]}...' ({len(current_explanation)} chars)"
        )
        print(
            f"New explanation:     '{que_en_solution[:100]}...' ({len(que_en_solution)} chars)"
        )

    if len(candidates) > preview_limit:
        print(f"\n... and {len(candidates) - preview_limit} more records")


def backup_postgres_table():
    """Create a backup of the problems table"""
    backup_file = f"/tmp/problems_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    print("\n" + "=" * 80)
    print("STEP 3: Creating backup...")
    print("=" * 80)
    print(f"\nBackup file: {backup_file}")

    import subprocess

    cmd = [
        "pg_dump",
        "-h",
        POSTGRES_CONFIG["host"],
        "-U",
        POSTGRES_CONFIG["user"],
        "-d",
        POSTGRES_CONFIG["dbname"],
        "-t",
        "problems",
        "-f",
        backup_file,
    ]

    env = {"PGPASSWORD": POSTGRES_CONFIG["password"]}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✓ Backup created successfully: {backup_file}")
        return backup_file
    else:
        print(f"✗ Backup failed: {result.stderr}")
        return None


def execute_backfill(candidates: List[Tuple[int, str, str]], dry_run: bool = True):
    """Execute the backfill operation"""
    if dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - Showing SQL that would be executed")
        print("=" * 80)

        for mysql_id, _, que_en_solution in candidates[:5]:
            # Escape for display
            safe_solution = que_en_solution.replace("'", "''")[:100]
            print(
                f"""
UPDATE problems 
SET mysql_metadata = jsonb_set(
    mysql_metadata, 
    '{{explanation}}', 
    to_jsonb('{safe_solution}...'::text)
)
WHERE (mysql_metadata->>'mysql_id')::int = {mysql_id};
"""
            )

        if len(candidates) > 5:
            print(f"... and {len(candidates) - 5} more UPDATE statements")

        print(f"\nTotal records to update: {len(candidates)}")
        print("\n⚠ This is a DRY RUN. Use --execute to actually perform the update.")
        return

    # Actually execute
    print("\n" + "=" * 80)
    print("STEP 4: Executing backfill...")
    print("=" * 80)

    pg_conn = get_postgres_connection()
    pg_conn.autocommit = False  # Use transaction

    try:
        with pg_conn.cursor() as cursor:
            updated_count = 0
            failed_count = 0

            for mysql_id, _, que_en_solution in candidates:
                try:
                    cursor.execute(
                        """
                        UPDATE problems 
                        SET mysql_metadata = jsonb_set(
                            mysql_metadata, 
                            '{explanation}', 
                            to_jsonb(%s::text),
                            true
                        ),
                        updated_at = NOW()
                        WHERE (mysql_metadata->>'mysql_id')::int = %s
                    """,
                        (que_en_solution, mysql_id),
                    )

                    updated_count += cursor.rowcount

                    if updated_count % 100 == 0:
                        print(
                            f"Progress: {updated_count}/{len(candidates)} records updated..."
                        )

                except Exception as e:
                    print(f"✗ Failed to update mysql_id {mysql_id}: {e}")
                    failed_count += 1

            # Commit transaction
            pg_conn.commit()

            print("\n" + "=" * 80)
            print("RESULTS")
            print("=" * 80)
            print(f"✓ Successfully updated: {updated_count} records")
            if failed_count > 0:
                print(f"✗ Failed: {failed_count} records")

            # Verify some records
            print("\nVerifying random samples...")
            sample_ids = [c[0] for c in candidates[:3]]
            for mysql_id in sample_ids:
                cursor.execute(
                    """
                    SELECT 
                        id,
                        (mysql_metadata->>'mysql_id')::int as mysql_id,
                        LENGTH(mysql_metadata->>'explanation') as explanation_length
                    FROM problems
                    WHERE (mysql_metadata->>'mysql_id')::int = %s
                """,
                    (mysql_id,),
                )
                row = cursor.fetchone()
                if row:
                    print(f"  mysql_id {mysql_id}: explanation length = {row[2]} chars")

    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        print("Rolling back transaction...")
        pg_conn.rollback()
        raise

    finally:
        pg_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill explanation from MySQL to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the update (default is dry-run)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of records to process"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating backup (not recommended)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("PostgreSQL Explanation Backfill Tool")
    print("=" * 80)
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"Limit: {args.limit if args.limit else 'None'}")
    print(f"Backup: {'Disabled' if args.skip_backup else 'Enabled'}")
    print()

    # Check dependencies
    for pkg in ("pymysql", "psycopg"):
        if importlib.util.find_spec(pkg) is None:
            print(f" Missing dependency: {pkg}")
            print("\nInstall required packages:")
            print("  pip install pymysql psycopg psycopg-binary")
            sys.exit(1)

    # Find candidates
    try:
        candidates = find_candidates(limit=args.limit)
    except Exception as e:
        print(f"\n Error finding candidates: {e}")
        sys.exit(1)

    if not candidates:
        print("\n✓ No records need backfilling. All done!")
        return

    # Preview changes
    preview_changes(candidates)

    # Create backup (unless skipped or dry-run)
    if args.execute and not args.skip_backup:
        backup_file = backup_postgres_table()
        if not backup_file:
            print("\n✗ Backup failed. Aborting for safety.")
            sys.exit(1)

    # Execute or show dry-run
    execute_backfill(candidates, dry_run=not args.execute)

    if not args.execute:
        print("\n" + "=" * 80)
        print("To actually execute the backfill, run:")
        print(f"  python {sys.argv[0]} --execute")
        if args.limit:
            print(f"  python {sys.argv[0]} --execute --limit {args.limit}")
        print("=" * 80)


if __name__ == "__main__":
    main()
