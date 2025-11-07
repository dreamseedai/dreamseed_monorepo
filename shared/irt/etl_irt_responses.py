#!/usr/bin/env python3
"""
IRT Response Data ETL Pipeline
===============================
Extract response data, transform for calibration, load into windows

Usage:
    python -m shared.irt.etl_irt_responses --window-label "2025-10 monthly" \
        --start-date 2025-10-01 --end-date 2025-10-31 \
        --population-tags cohort:2025-Q4 country:KR lang:ko
"""
import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional

import asyncpg
import click
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================
class ETLConfig(BaseModel):
    """ETL configuration"""
    database_url: str
    min_responses_per_item: int = 30  # Minimum responses for calibration
    min_variance: float = 0.05  # Minimum response variance (exclude perfect items)
    
    class Config:
        env_prefix = 'IRT_ETL_'


# ============================================================================
# Data Models
# ============================================================================
class WindowSpec(BaseModel):
    """Calibration window specification"""
    label: str
    start_at: datetime
    end_at: datetime
    population_tags: List[str] = []


class ItemResponseSummary(BaseModel):
    """Summary statistics for an item in a window"""
    item_id: int
    n_responses: int
    mean_correct: float
    variance: float
    users_count: int


# ============================================================================
# Database Operations
# ============================================================================
class IRTDatabase:
    """IRT database operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created")
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def create_window(self, spec: WindowSpec) -> int:
        """Create or get window ID"""
        async with self.pool.acquire() as conn:
            # Check if window exists
            row = await conn.fetchrow(
                """
                SELECT id FROM shared_irt.windows WHERE label = $1
                """,
                spec.label
            )
            
            if row:
                logger.info(f"Window '{spec.label}' already exists (id={row['id']})")
                return row['id']
            
            # Create new window
            row = await conn.fetchrow(
                """
                INSERT INTO shared_irt.windows (label, start_at, end_at, population_tags)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                spec.label,
                spec.start_at,
                spec.end_at,
                spec.population_tags
            )
            
            window_id = row['id']
            logger.info(f"Created window '{spec.label}' (id={window_id})")
            return window_id
    
    async def extract_responses(
        self,
        start_at: datetime,
        end_at: datetime,
        population_tags: List[str]
    ) -> List[dict]:
        """
        Extract responses within window and population filters
        
        Returns list of dicts with: item_id, user_id_hash, is_correct, score, answered_at
        """
        # Build WHERE clause for population_tags
        # Example tag format: "cohort:2025-Q4", "country:KR", "lang:ko"
        tag_filters = []
        params = [start_at, end_at]
        param_idx = 3
        
        for tag in population_tags:
            if ':' in tag:
                key, value = tag.split(':', 1)
                if key == 'lang':
                    tag_filters.append(f"lang = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                elif key == 'org_id':
                    tag_filters.append(f"org_id = ${param_idx}")
                    params.append(value)
                    param_idx += 1
                # Add more tag filters as needed (via extra JSONB column)
        
        where_clause = "answered_at >= $1 AND answered_at < $2"
        if tag_filters:
            where_clause += " AND " + " AND ".join(tag_filters)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT 
                    item_id,
                    user_id_hash,
                    is_correct,
                    score,
                    answered_at,
                    lang,
                    org_id
                FROM shared_irt.item_responses
                WHERE {where_clause}
                ORDER BY item_id, user_id_hash, answered_at
                """,
                *params
            )
        
        logger.info(f"Extracted {len(rows)} responses from {start_at} to {end_at}")
        return [dict(row) for row in rows]
    
    async def get_item_response_summary(
        self,
        responses: List[dict],
        min_responses: int,
        min_variance: float
    ) -> List[ItemResponseSummary]:
        """
        Aggregate responses by item and filter based on quality criteria
        """
        from collections import defaultdict
        import statistics
        
        item_data = defaultdict(lambda: {'correct': [], 'users': set()})
        
        for resp in responses:
            item_id = resp['item_id']
            is_correct = resp['is_correct']
            user_hash = resp['user_id_hash']
            
            if is_correct is not None:
                item_data[item_id]['correct'].append(1 if is_correct else 0)
                item_data[item_id]['users'].add(user_hash)
        
        summaries = []
        for item_id, data in item_data.items():
            correct_list = data['correct']
            n = len(correct_list)
            
            if n < min_responses:
                logger.debug(f"Item {item_id}: insufficient responses ({n} < {min_responses})")
                continue
            
            mean_correct = statistics.mean(correct_list)
            variance = statistics.variance(correct_list) if n > 1 else 0.0
            
            if variance < min_variance:
                logger.debug(f"Item {item_id}: low variance ({variance:.4f} < {min_variance})")
                continue
            
            summaries.append(ItemResponseSummary(
                item_id=item_id,
                n_responses=n,
                mean_correct=mean_correct,
                variance=variance,
                users_count=len(data['users'])
            ))
        
        logger.info(f"Filtered to {len(summaries)} items meeting quality criteria")
        return summaries
    
    async def export_calibration_data(
        self,
        window_id: int,
        start_at: datetime,
        end_at: datetime,
        population_tags: List[str],
        output_path: str
    ):
        """
        Export response matrix for R calibration script
        
        Format: CSV with columns [user_id_hash, item_id, is_correct]
        """
        import csv
        
        responses = await self.extract_responses(start_at, end_at, population_tags)
        
        # Filter to one response per user-item (take latest)
        user_item_map = {}
        for resp in responses:
            key = (resp['user_id_hash'], resp['item_id'])
            if key not in user_item_map or resp['answered_at'] > user_item_map[key]['answered_at']:
                user_item_map[key] = resp
        
        unique_responses = list(user_item_map.values())
        logger.info(f"Deduplicated to {len(unique_responses)} unique user-item responses")
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id_hash', 'item_id', 'is_correct'])
            writer.writeheader()
            
            for resp in unique_responses:
                if resp['is_correct'] is not None:
                    writer.writerow({
                        'user_id_hash': resp['user_id_hash'],
                        'item_id': resp['item_id'],
                        'is_correct': 1 if resp['is_correct'] else 0
                    })
        
        logger.info(f"Exported calibration data to {output_path}")


# ============================================================================
# ETL Orchestration
# ============================================================================
async def run_etl(
    database_url: str,
    window_spec: WindowSpec,
    min_responses: int = 30,
    min_variance: float = 0.05,
    output_path: Optional[str] = None
):
    """Run full ETL pipeline"""
    db = IRTDatabase(database_url)
    
    try:
        await db.connect()
        
        # Step 1: Create window
        window_id = await db.create_window(window_spec)
        
        # Step 2: Extract responses
        responses = await db.extract_responses(
            window_spec.start_at,
            window_spec.end_at,
            window_spec.population_tags
        )
        
        if not responses:
            logger.warning("No responses found for this window")
            return
        
        # Step 3: Validate item quality
        summaries = await db.get_item_response_summary(
            responses,
            min_responses,
            min_variance
        )
        
        logger.info(f"Window {window_id} summary: {len(summaries)} items ready for calibration")
        
        # Step 4: Export calibration data
        if output_path:
            await db.export_calibration_data(
                window_id,
                window_spec.start_at,
                window_spec.end_at,
                window_spec.population_tags,
                output_path
            )
        
    finally:
        await db.close()


# ============================================================================
# CLI Interface
# ============================================================================
@click.command()
@click.option('--database-url', envvar='DATABASE_URL', required=True, help='PostgreSQL connection string')
@click.option('--window-label', required=True, help='Window label (e.g., "2025-10 monthly")')
@click.option('--start-date', required=True, help='Window start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='Window end date (YYYY-MM-DD)')
@click.option('--population-tags', multiple=True, help='Population filters (e.g., "cohort:2025-Q4", "lang:ko")')
@click.option('--min-responses', default=30, help='Minimum responses per item')
@click.option('--min-variance', default=0.05, help='Minimum response variance')
@click.option('--output', help='Output CSV path for calibration data')
def main(
    database_url: str,
    window_label: str,
    start_date: str,
    end_date: str,
    population_tags: tuple,
    min_responses: int,
    min_variance: float,
    output: Optional[str]
):
    """Run IRT response data ETL pipeline"""
    
    # Parse dates
    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    
    # Create window spec
    window_spec = WindowSpec(
        label=window_label,
        start_at=start_dt,
        end_at=end_dt,
        population_tags=list(population_tags)
    )
    
    # Run ETL
    asyncio.run(run_etl(
        database_url,
        window_spec,
        min_responses,
        min_variance,
        output
    ))


if __name__ == '__main__':
    main()
