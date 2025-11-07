#!/usr/bin/env python3
"""
IRT Calibration Python Wrapper
================================
Orchestrates R calibration script and stores results in PostgreSQL

Usage:
    python -m shared.irt.calibrate_irt --window-id 1 --model 2PL
"""
import asyncio
import json
import logging
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import asyncpg
import click

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class IRTCalibrator:
    """IRT calibration orchestrator"""
    
    def __init__(self, database_url: str, r_script_path: str):
        self.database_url = database_url
        self.r_script_path = r_script_path
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=120
        )
        logger.info("Database connected")
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
    
    async def export_responses_for_window(
        self,
        window_id: int,
        output_csv: str
    ) -> int:
        """Export responses for calibration window"""
        async with self.pool.acquire() as conn:
            # Get window metadata
            window = await conn.fetchrow(
                "SELECT start_at, end_at, population_tags FROM shared_irt.windows WHERE id = $1",
                window_id
            )
            
            if not window:
                raise ValueError(f"Window {window_id} not found")
            
            # Build population filter
            tag_filters = []
            params = [window['start_at'], window['end_at']]
            param_idx = 3
            
            for tag in window['population_tags']:
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
            
            where_clause = "answered_at >= $1 AND answered_at < $2"
            if tag_filters:
                where_clause += " AND " + " AND ".join(tag_filters)
            
            # Export responses
            query = f"""
            COPY (
                SELECT user_id_hash, item_id, 
                       CASE WHEN is_correct THEN 1 ELSE 0 END as is_correct
                FROM shared_irt.item_responses
                WHERE {where_clause}
            ) TO STDOUT WITH CSV HEADER
            """
            
            with open(output_csv, 'wb') as f:
                await conn.copy_from_query(query, output=f, format='csv')
            
            # Count responses
            count_query = f"""
            SELECT COUNT(*) as n
            FROM shared_irt.item_responses
            WHERE {where_clause}
            """
            
            result = await conn.fetchrow(count_query, *params)
            n_responses = result['n']
            
            logger.info(f"Exported {n_responses} responses to {output_csv}")
            return n_responses
    
    async def get_previous_params(self, window_id: int, output_json: str) -> bool:
        """Get previous window params if exists"""
        async with self.pool.acquire() as conn:
            # Find previous window (by created_at)
            prev_window = await conn.fetchrow(
                """
                SELECT id FROM shared_irt.windows
                WHERE created_at < (SELECT created_at FROM shared_irt.windows WHERE id = $1)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                window_id
            )
            
            if not prev_window:
                logger.info("No previous window found")
                return False
            
            prev_window_id = prev_window['id']
            
            # Get previous calibration params
            params = await conn.fetch(
                """
                SELECT item_id, model, a_hat as a, b_hat as b, c_hat as c
                FROM shared_irt.item_calibration
                WHERE window_id = $1
                """,
                prev_window_id
            )
            
            if not params:
                logger.info(f"No previous calibration found for window {prev_window_id}")
                return False
            
            # Export to JSON
            params_dict = {
                "window_id": prev_window_id,
                "parameters": [dict(row) for row in params]
            }
            
            with open(output_json, 'w') as f:
                json.dump(params_dict, f)
            
            logger.info(f"Loaded previous params from window {prev_window_id}")
            return True
    
    def run_r_calibration(
        self,
        input_csv: str,
        output_json: str,
        model: str,
        previous_json: Optional[str] = None
    ):
        """Run R calibration script"""
        cmd = [
            'Rscript',
            self.r_script_path,
            '--input', input_csv,
            '--model', model,
            '--output', output_json
        ]
        
        if previous_json and Path(previous_json).exists():
            cmd.extend(['--previous', previous_json])
        
        logger.info(f"Running R calibration: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes max
        )
        
        if result.returncode != 0:
            logger.error(f"R script stderr:\n{result.stderr}")
            raise RuntimeError(f"R calibration failed with code {result.returncode}")
        
        logger.info("R calibration completed successfully")
        logger.debug(f"R script output:\n{result.stdout}")
    
    async def store_calibration_results(
        self,
        window_id: int,
        results_json: str
    ):
        """Store calibration results and create drift alerts"""
        with open(results_json) as f:
            results = json.load(f)
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Store calibration results
                for param in results['parameters']:
                    await conn.execute(
                        """
                        INSERT INTO shared_irt.item_calibration
                        (item_id, window_id, model, a_hat, b_hat, c_hat, 
                         n_responses, loglik, drift_flag)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (item_id, window_id) DO UPDATE SET
                            model = EXCLUDED.model,
                            a_hat = EXCLUDED.a_hat,
                            b_hat = EXCLUDED.b_hat,
                            c_hat = EXCLUDED.c_hat,
                            n_responses = EXCLUDED.n_responses,
                            loglik = EXCLUDED.loglik,
                            drift_flag = EXCLUDED.drift_flag,
                            created_at = now()
                        """,
                        param['item_id'],
                        window_id,
                        param['model'],
                        param.get('a'),
                        param['b'],
                        param.get('c'),
                        param['n_responses'],
                        results.get('loglik'),
                        param.get('drift_flag')
                    )
                
                # Create drift alerts for flagged items
                for param in results['parameters']:
                    if param.get('drift_flag'):
                        drift_metric = param['drift_flag']
                        drift_value = param.get(f'delta_{drift_metric}')
                        
                        if drift_value is None:
                            continue
                        
                        # Determine severity
                        abs_drift = abs(drift_value)
                        if abs_drift > 0.5:
                            severity = 'high'
                        elif abs_drift > 0.3:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        message = (
                            f"Item {param['item_id']}: {drift_metric} parameter drifted by "
                            f"{drift_value:.3f} (current: {param[drift_metric]:.3f})"
                        )
                        
                        await conn.execute(
                            """
                            INSERT INTO shared_irt.drift_alerts
                            (item_id, window_id, metric, value, threshold, severity, message)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            param['item_id'],
                            window_id,
                            f'Δ{drift_metric}',
                            drift_value,
                            0.3 if drift_metric == 'b' else 0.5,
                            severity,
                            message
                        )
                
                logger.info(f"Stored calibration results for window {window_id}")
                
                # Update current parameters for non-drifted anchor items
                await conn.execute(
                    """
                    INSERT INTO shared_irt.item_parameters_current
                    (item_id, model, a, b, c, version, effective_from)
                    SELECT 
                        ic.item_id,
                        ic.model,
                        ic.a_hat,
                        ic.b_hat,
                        ic.c_hat,
                        COALESCE((SELECT version FROM shared_irt.item_parameters_current WHERE item_id = ic.item_id), 0) + 1,
                        now()
                    FROM shared_irt.item_calibration ic
                    JOIN shared_irt.items i ON ic.item_id = i.id
                    WHERE ic.window_id = $1
                      AND (ic.drift_flag IS NULL OR i.is_anchor = FALSE)
                    ON CONFLICT (item_id) DO UPDATE SET
                        model = EXCLUDED.model,
                        a = EXCLUDED.a,
                        b = EXCLUDED.b,
                        c = EXCLUDED.c,
                        version = EXCLUDED.version,
                        effective_from = EXCLUDED.effective_from,
                        updated_at = now()
                    """,
                    window_id
                )
                
                logger.info("Updated current parameters for non-drifted items")
    
    async def calibrate_window(
        self,
        window_id: int,
        model: str = '2PL'
    ):
        """Full calibration workflow for a window"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Step 1: Export responses
            input_csv = tmppath / 'responses.csv'
            n_responses = await self.export_responses_for_window(window_id, str(input_csv))
            
            if n_responses == 0:
                raise ValueError(f"No responses found for window {window_id}")
            
            # Step 2: Get previous params (if any)
            previous_json = tmppath / 'previous_params.json'
            has_previous = await self.get_previous_params(window_id, str(previous_json))
            
            # Step 3: Run R calibration
            output_json = tmppath / 'calibration_results.json'
            self.run_r_calibration(
                str(input_csv),
                str(output_json),
                model,
                str(previous_json) if has_previous else None
            )
            
            # Step 4: Store results
            await self.store_calibration_results(window_id, str(output_json))
            
            logger.info(f"✓ Calibration complete for window {window_id}")


@click.command()
@click.option('--database-url', envvar='DATABASE_URL', required=True)
@click.option('--window-id', type=int, required=True, help='Window ID to calibrate')
@click.option('--model', default='2PL', type=click.Choice(['1PL', '2PL', '3PL']),
              help='IRT model to fit')
@click.option('--r-script', default=None, help='Path to calibrate_irt.R script')
def main(database_url: str, window_id: int, model: str, r_script: Optional[str]):
    """Run IRT calibration for a window"""
    
    # Locate R script
    if r_script is None:
        r_script = str(Path(__file__).parent / 'calibrate_irt.R')
    
    if not Path(r_script).exists():
        raise FileNotFoundError(f"R script not found: {r_script}")
    
    # Run calibration
    calibrator = IRTCalibrator(database_url, r_script)
    
    async def run():
        try:
            await calibrator.connect()
            await calibrator.calibrate_window(window_id, model)
        finally:
            await calibrator.close()
    
    asyncio.run(run())


if __name__ == '__main__':
    main()
