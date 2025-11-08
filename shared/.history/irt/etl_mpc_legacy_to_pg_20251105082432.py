#!/usr/bin/env python3
"""
ETL: MPC Legacy MySQL → PostgreSQL IRT Items
=============================================
Migrates legacy MPC items from MySQL to shared_irt.items table

Features:
- Wiris MathML → LaTeX conversion (placeholder)
- HTML → TipTap JSON structure
- MCQ options formatting
- Tag migration
- Idempotent (ON CONFLICT DO UPDATE)

Usage:
    python -m shared.irt.etl_mpc_legacy_to_pg \
        --mysql-host 127.0.0.1 \
        --mysql-user root \
        --mysql-password *** \
        --mysql-db mpc_legacy \
        --pg-host 127.0.0.1 \
        --pg-user postgres \
        --pg-password *** \
        --pg-dbname dreamseed \
        --batch-size 100 \
        --dry-run

Environment Variables:
    MPC_MYSQL_HOST, MPC_MYSQL_USER, MPC_MYSQL_PASSWORD, MPC_MYSQL_DB
    POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DBNAME
"""
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import click

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    raise ImportError("Install pymysql: pip install pymysql")

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    raise ImportError("Install psycopg2: pip install psycopg2-binary")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Content Conversion Functions
# ==============================================================================

def wiris_to_mathlive(html: str) -> str:
    """
    Convert Wiris MathML to LaTeX for MathLive
    
    Note: This is a placeholder. In production, use a proper MathML→LaTeX converter
    such as:
    - lxml.etree for parsing MathML
    - sympy.printing.latex for conversion
    - mathml2latex library
    
    Example proper implementation:
        from mathml2latex import convert
        latex = convert(mathml_string)
    """
    # Normalize whitespace
    html = re.sub(r'\s+', ' ', html)
    
    # Extract MathML blocks
    mathml_blocks = re.findall(r'(<math.*?</math>)', html, flags=re.I | re.S)
    
    if not mathml_blocks:
        return html
    
    # TODO: Replace with actual MathML→LaTeX conversion
    # For now, wrap in LaTeX delimiters
    for mathml in mathml_blocks:
        # Placeholder: extract text content from MathML
        text_content = re.sub(r'<[^<]+?>', '', mathml).strip()
        latex = f"${{{text_content}}}$"  # Wrap in inline math
        html = html.replace(mathml, latex)
        logger.debug(f"Converted MathML block to LaTeX placeholder: {latex}")
    
    return html


def html_to_tiptap_nodes(html: str) -> Dict:
    """
    Convert HTML to TipTap JSON structure
    
    Note: This is a simplified version. For production, use:
    - BeautifulSoup for HTML parsing
    - html2tiptap library
    - or TipTap's built-in HTML parser
    
    Example proper implementation:
        from html2tiptap import HTML2TipTap
        converter = HTML2TipTap()
        tiptap_json = converter.convert(html)
    """
    # Strip HTML tags for now (placeholder)
    text = re.sub(r'<[^<]+?>', ' ', html).strip()
    text = re.sub(r'\s+', ' ', text)
    
    if not text:
        return {"type": "doc", "content": []}
    
    # Basic TipTap structure
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }


def options_to_tiptap(options: List[str]) -> Dict:
    """
    Convert MCQ options list to TipTap JSON
    
    Args:
        options: List of option texts (HTML strings)
    
    Returns:
        TipTap doc with paragraph per option
    """
    if not options:
        return {"type": "doc", "content": []}
    
    content = []
    for i, opt_html in enumerate(options, 1):
        # Strip HTML tags
        opt_text = re.sub(r'<[^<]+?>', ' ', opt_html).strip()
        opt_text = re.sub(r'\s+', ' ', opt_text)
        
        content.append({
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": f"{i}. {opt_text}"
                }
            ]
        })
    
    return {"type": "doc", "content": content}


# ==============================================================================
# ETL Pipeline
# ==============================================================================

class MPCLegacyETL:
    """ETL pipeline for MPC legacy data"""
    
    def __init__(
        self,
        mysql_config: Dict[str, str],
        pg_config: Dict[str, str],
        batch_size: int = 100,
        dry_run: bool = False
    ):
        self.mysql_config = mysql_config
        self.pg_config = pg_config
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.stats = {
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "errors": 0
        }
    
    def connect_mysql(self) -> Tuple[pymysql.Connection, pymysql.cursors.DictCursor]:
        """Connect to MySQL"""
        conn = pymysql.connect(
            host=self.mysql_config['host'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            db=self.mysql_config['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        logger.info(f"Connected to MySQL: {self.mysql_config['host']}/{self.mysql_config['db']}")
        return conn, cursor
    
    def connect_pg(self) -> Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
        """Connect to PostgreSQL"""
        conn = psycopg2.connect(
            host=self.pg_config['host'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            dbname=self.pg_config['dbname']
        )
        cursor = conn.cursor()
        logger.info(f"Connected to PostgreSQL: {self.pg_config['host']}/{self.pg_config['dbname']}")
        return conn, cursor
    
    def extract_items(self, mysql_cursor: pymysql.cursors.DictCursor) -> List[Dict]:
        """Extract items from MySQL"""
        query = """
        SELECT 
            id, 
            subject, 
            lang, 
            stem_html, 
            options_html, 
            answer, 
            tags,
            created_at,
            updated_at
        FROM mpc_items
        ORDER BY id
        """
        
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()
        
        logger.info(f"Extracted {len(rows)} items from MySQL")
        return rows
    
    def transform_item(self, row: Dict) -> Optional[Dict]:
        """Transform MySQL row to PostgreSQL format"""
        try:
            # Convert stem HTML
            stem_html = row.get('stem_html', '')
            if stem_html:
                stem_html = wiris_to_mathlive(stem_html)
            stem_rich = html_to_tiptap_nodes(stem_html)
            
            # Parse and convert options
            options_html = row.get('options_html', '')
            if options_html:
                try:
                    opt_list = json.loads(options_html)
                    if isinstance(opt_list, str):
                        opt_list = [options_html]
                except json.JSONDecodeError:
                    opt_list = [options_html]
            else:
                opt_list = []
            
            options_rich = options_to_tiptap(opt_list)
            
            # Parse tags
            tags_str = row.get('tags', '')
            topic_tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
            
            # Build answer key
            answer_key = {
                "type": "mcq",
                "correct": row.get('answer', 1)
            }
            
            # Build metadata
            metadata = {
                "source": "mpc_legacy",
                "legacy_id": row['id'],
                "migrated_at": datetime.utcnow().isoformat()
            }
            
            if row.get('created_at'):
                metadata['legacy_created_at'] = row['created_at'].isoformat() if isinstance(row['created_at'], datetime) else str(row['created_at'])
            
            return {
                'id_str': f"mpc_{row['id']}",
                'bank_id': row.get('subject') or 'mpc_legacy',
                'lang': row.get('lang') or 'ko',
                'stem_rich': stem_rich,
                'options_rich': options_rich,
                'answer_key': answer_key,
                'topic_tags': topic_tags,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to transform item {row.get('id')}: {e}")
            return None
    
    def load_item(self, pg_cursor: psycopg2.extensions.cursor, item: Dict) -> bool:
        """Load item into PostgreSQL"""
        try:
            query = """
            INSERT INTO shared_irt.items (
                id_str, bank_id, lang, stem_rich, options_rich, 
                answer_key, topic_tags, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_str) DO UPDATE SET
                bank_id = EXCLUDED.bank_id,
                lang = EXCLUDED.lang,
                stem_rich = EXCLUDED.stem_rich,
                options_rich = EXCLUDED.options_rich,
                answer_key = EXCLUDED.answer_key,
                topic_tags = EXCLUDED.topic_tags,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, (xmax = 0) AS inserted
            """
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would insert/update: {item['id_str']}")
                return True
            
            pg_cursor.execute(query, (
                item['id_str'],
                item['bank_id'],
                item['lang'],
                Json(item['stem_rich']),
                Json(item['options_rich']),
                Json(item['answer_key']),
                item['topic_tags'],
                Json(item['metadata'])
            ))
            
            result = pg_cursor.fetchone()
            if result:
                item_id, inserted = result
                if inserted:
                    self.stats['inserted'] += 1
                    logger.debug(f"Inserted: {item['id_str']} (id={item_id})")
                else:
                    self.stats['updated'] += 1
                    logger.debug(f"Updated: {item['id_str']} (id={item_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load item {item['id_str']}: {e}")
            self.stats['errors'] += 1
            return False
    
    def run(self):
        """Run full ETL pipeline"""
        logger.info("Starting MPC legacy ETL...")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        
        my_conn, my_cursor = self.connect_mysql()
        pg_conn, pg_cursor = self.connect_pg()
        
        try:
            # Extract
            rows = self.extract_items(my_cursor)
            self.stats['total'] = len(rows)
            
            # Transform & Load
            for i, row in enumerate(rows, 1):
                item = self.transform_item(row)
                
                if item:
                    self.load_item(pg_cursor, item)
                else:
                    self.stats['errors'] += 1
                
                if i % self.batch_size == 0:
                    if not self.dry_run:
                        pg_conn.commit()
                    logger.info(f"Processed {i}/{self.stats['total']} items...")
            
            # Final commit
            if not self.dry_run:
                pg_conn.commit()
            
            logger.info("ETL complete!")
            logger.info(f"Total: {self.stats['total']}")
            logger.info(f"Inserted: {self.stats['inserted']}")
            logger.info(f"Updated: {self.stats['updated']}")
            logger.info(f"Errors: {self.stats['errors']}")
            
        except Exception as e:
            logger.error(f"ETL failed: {e}")
            if not self.dry_run:
                pg_conn.rollback()
            raise
        
        finally:
            my_cursor.close()
            my_conn.close()
            pg_cursor.close()
            pg_conn.close()


# ==============================================================================
# CLI
# ==============================================================================

@click.command()
@click.option('--mysql-host', envvar='MPC_MYSQL_HOST', default='127.0.0.1', help='MySQL host')
@click.option('--mysql-user', envvar='MPC_MYSQL_USER', default='root', help='MySQL user')
@click.option('--mysql-password', envvar='MPC_MYSQL_PASSWORD', required=True, help='MySQL password')
@click.option('--mysql-db', envvar='MPC_MYSQL_DB', default='mpc_legacy', help='MySQL database')
@click.option('--pg-host', envvar='POSTGRES_HOST', default='127.0.0.1', help='PostgreSQL host')
@click.option('--pg-user', envvar='POSTGRES_USER', default='postgres', help='PostgreSQL user')
@click.option('--pg-password', envvar='POSTGRES_PASSWORD', required=True, help='PostgreSQL password')
@click.option('--pg-dbname', envvar='POSTGRES_DBNAME', default='dreamseed', help='PostgreSQL database')
@click.option('--batch-size', default=100, help='Commit batch size')
@click.option('--dry-run', is_flag=True, help='Dry run (no writes)')
def main(
    mysql_host: str,
    mysql_user: str,
    mysql_password: str,
    mysql_db: str,
    pg_host: str,
    pg_user: str,
    pg_password: str,
    pg_dbname: str,
    batch_size: int,
    dry_run: bool
):
    """Migrate MPC legacy items from MySQL to PostgreSQL IRT schema"""
    
    mysql_config = {
        'host': mysql_host,
        'user': mysql_user,
        'password': mysql_password,
        'db': mysql_db
    }
    
    pg_config = {
        'host': pg_host,
        'user': pg_user,
        'password': pg_password,
        'dbname': pg_dbname
    }
    
    etl = MPCLegacyETL(mysql_config, pg_config, batch_size, dry_run)
    etl.run()


if __name__ == "__main__":
    main()
