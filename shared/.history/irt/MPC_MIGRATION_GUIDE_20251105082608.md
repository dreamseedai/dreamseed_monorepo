# MPC Legacy Migration Guide

## Overview

Migrate legacy MPC items from MySQL to PostgreSQL `shared_irt` schema with automatic content conversion.

## Prerequisites

```bash
# Install dependencies
pip install pymysql psycopg2-binary click

# Optional: For proper MathML→LaTeX conversion
pip install mathml2latex lxml
```

## Quick Start

### 1. Dry Run (recommended first)

```bash
python -m shared.irt.etl_mpc_legacy_to_pg \
  --mysql-host 127.0.0.1 \
  --mysql-user root \
  --mysql-password YOUR_MYSQL_PASSWORD \
  --mysql-db mpc_legacy \
  --pg-host 127.0.0.1 \
  --pg-user postgres \
  --pg-password YOUR_PG_PASSWORD \
  --pg-dbname dreamseed \
  --dry-run

# Expected output:
# [INFO] Starting MPC legacy ETL...
# [INFO] Mode: DRY RUN
# [INFO] Connected to MySQL: 127.0.0.1/mpc_legacy
# [INFO] Connected to PostgreSQL: 127.0.0.1/dreamseed
# [INFO] Extracted 1234 items from MySQL
# [INFO] Processed 100/1234 items...
# ...
# [INFO] ETL complete!
# [INFO] Total: 1234
# [INFO] Inserted: 0
# [INFO] Updated: 0
# [INFO] Errors: 0
```

### 2. Live Migration

```bash
python -m shared.irt.etl_mpc_legacy_to_pg \
  --mysql-host 127.0.0.1 \
  --mysql-user root \
  --mysql-password YOUR_MYSQL_PASSWORD \
  --mysql-db mpc_legacy \
  --pg-host 127.0.0.1 \
  --pg-user postgres \
  --pg-password YOUR_PG_PASSWORD \
  --pg-dbname dreamseed \
  --batch-size 100

# Expected output:
# [INFO] Starting MPC legacy ETL...
# [INFO] Mode: LIVE
# [INFO] Total: 1234
# [INFO] Inserted: 1234
# [INFO] Updated: 0
# [INFO] Errors: 0
```

### 3. Re-run (idempotent)

```bash
# Subsequent runs will UPDATE existing items
python -m shared.irt.etl_mpc_legacy_to_pg \
  --mysql-password *** \
  --pg-password ***

# Output:
# [INFO] Total: 1234
# [INFO] Inserted: 0
# [INFO] Updated: 1234  # Items with id_str='mpc_*' are updated
# [INFO] Errors: 0
```

## Environment Variables

Instead of CLI options, use environment variables:

```bash
export MPC_MYSQL_HOST=127.0.0.1
export MPC_MYSQL_USER=root
export MPC_MYSQL_PASSWORD=***
export MPC_MYSQL_DB=mpc_legacy

export POSTGRES_HOST=127.0.0.1
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=***
export POSTGRES_DBNAME=dreamseed

python -m shared.irt.etl_mpc_legacy_to_pg
```

## Data Mapping

### MySQL → PostgreSQL

| MySQL Column | PostgreSQL Column | Transformation |
|--------------|-------------------|----------------|
| `id` | `id_str` (as `mpc_{id}`) | String prefix |
| `subject` | `bank_id` | Direct (fallback: `mpc_legacy`) |
| `lang` | `lang` | Direct (fallback: `ko`) |
| `stem_html` | `stem_rich` | Wiris→LaTeX, HTML→TipTap JSON |
| `options_html` | `options_rich` | JSON array→TipTap JSON |
| `answer` | `answer_key` | `{"type":"mcq","correct":N}` |
| `tags` | `topic_tags` | CSV string→Array |
| - | `metadata` | `{"source":"mpc_legacy","legacy_id":N}` |

### Content Conversion

**Wiris MathML → LaTeX:**
```html
<!-- Input (MySQL) -->
<math><mi>x</mi><mo>+</mo><mn>2</mn><mo>=</mo><mn>5</mn></math>

<!-- Output (PostgreSQL stem_rich) -->
${x+2=5}$
```

**HTML → TipTap JSON:**
```html
<!-- Input (MySQL) -->
<p>Solve the equation: <b>x+2=5</b></p>

<!-- Output (PostgreSQL stem_rich) -->
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Solve the equation: x+2=5"}
      ]
    }
  ]
}
```

## Verify Migration

```sql
-- Check migrated items
SELECT 
  id_str,
  bank_id,
  lang,
  topic_tags,
  metadata->>'source' as source,
  metadata->>'legacy_id' as legacy_id,
  created_at
FROM shared_irt.items
WHERE id_str LIKE 'mpc_%'
LIMIT 10;

-- Count by bank
SELECT bank_id, COUNT(*) 
FROM shared_irt.items 
WHERE id_str LIKE 'mpc_%'
GROUP BY bank_id;

-- Check content structure
SELECT 
  id_str,
  stem_rich->'type' as stem_type,
  jsonb_array_length(stem_rich->'content') as stem_paragraphs,
  options_rich->'type' as options_type,
  jsonb_array_length(options_rich->'content') as num_options
FROM shared_irt.items
WHERE id_str = 'mpc_123';
```

## Troubleshooting

### Issue: "Import pymysql could not be resolved"

```bash
pip install pymysql
```

### Issue: "Failed to transform item: JSON decode error"

**Cause:** `options_html` contains invalid JSON

**Solution:** Check MySQL data
```sql
SELECT id, options_html 
FROM mpc_items 
WHERE options_html NOT LIKE '[%'
LIMIT 10;
```

### Issue: MathML conversion placeholder

**Solution:** Install proper converter
```bash
pip install mathml2latex

# Update etl_mpc_legacy_to_pg.py:
from mathml2latex import convert

def wiris_to_mathlive(html):
    mathml_blocks = re.findall(r'(<math.*?</math>)', html, re.I|re.S)
    for mathml in mathml_blocks:
        latex = convert(mathml)  # Proper conversion
        html = html.replace(mathml, f"${latex}$")
    return html
```

### Issue: "ON CONFLICT (id_str) constraint not found"

**Solution:** Run Alembic migration first
```bash
cd apps/seedtest_api
alembic upgrade head
```

## Advanced Usage

### Custom Bank Mapping

Edit `transform_item()` method:

```python
def transform_item(self, row: Dict) -> Optional[Dict]:
    # Custom subject→bank_id mapping
    subject_map = {
        'math': 'math-algebra',
        'eng': 'english-grammar',
        'sci': 'science-physics'
    }
    bank_id = subject_map.get(row.get('subject'), 'mpc_legacy')
    
    return {
        'bank_id': bank_id,
        # ... rest
    }
```

### Filter Migration

```python
def extract_items(self, mysql_cursor):
    query = """
    SELECT * FROM mpc_items
    WHERE subject = 'math'           -- Only math items
      AND lang = 'ko'                -- Only Korean
      AND created_at >= '2024-01-01' -- Recent items only
    ORDER BY id
    """
    mysql_cursor.execute(query)
    return mysql_cursor.fetchall()
```

### Custom Metadata

```python
metadata = {
    "source": "mpc_legacy",
    "legacy_id": row['id'],
    "migrated_at": datetime.utcnow().isoformat(),
    "difficulty": row.get('difficulty'),    # Add custom fields
    "author": row.get('author'),
    "review_status": row.get('status')
}
```

## Kubernetes Job

For production migration, use a K8s Job:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: mpc-migration
  namespace: seedtest
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest
        command:
        - python
        - -m
        - shared.irt.etl_mpc_legacy_to_pg
        env:
        - name: MPC_MYSQL_HOST
          value: "mysql.legacy.svc.cluster.local"
        - name: MPC_MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-credentials
              key: password
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: seedtest-api-credentials
              key: DATABASE_PASSWORD
      restartPolicy: OnFailure
```

## Post-Migration

1. **Verify counts match:**
   ```sql
   -- MySQL
   SELECT COUNT(*) FROM mpc_items;
   
   -- PostgreSQL
   SELECT COUNT(*) FROM shared_irt.items WHERE id_str LIKE 'mpc_%';
   ```

2. **Spot check content:**
   - Random sample comparison
   - Math rendering test
   - Option ordering verification

3. **Run calibration:**
   ```bash
   # ETL responses for migrated items
   python -m shared.irt.etl_irt_responses \
     --window-label "mpc-migration-baseline" \
     --start-date 2024-01-01 --end-date 2025-11-05
   
   # Calibrate
   python -m shared.irt.calibrate_irt --window-id 1 --model 2PL
   ```

## Rollback

```sql
-- Delete all migrated items
DELETE FROM shared_irt.items WHERE id_str LIKE 'mpc_%';

-- Verify
SELECT COUNT(*) FROM shared_irt.items;
```
