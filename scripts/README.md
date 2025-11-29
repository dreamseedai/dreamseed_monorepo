# Seed Data Scripts

## CAT Item Seeding

### Purpose
Generate test items with IRT parameters for CAT (Computerized Adaptive Testing) engine.

### Script: `seed_cat_items.py`

Generates **120 items** across 3 subjects with expert-estimated IRT parameters.

#### Features
- ✅ 3 subjects: Math, English, Science (40 items each)
- ✅ IRT parameters:
  - `a` (discrimination): 0.8 - 2.0
  - `b` (difficulty): -2.5 to +2.5 (normal distribution)
  - `c` (guessing): 0.15 - 0.25
- ✅ Multiple choice questions (4 options)
- ✅ Item pools for each subject
- ✅ Difficulty distribution: ~25% easy, ~50% medium, ~25% hard

#### Requirements
```bash
# 1. Database must be running
docker-compose up -d postgres  # or start PostgreSQL locally

# 2. Alembic migrations applied
cd backend
alembic upgrade head

# 3. Virtual environment activated
source .venv/bin/activate
```

#### Usage

**Basic usage:**
```bash
python scripts/seed_cat_items.py
```

**With custom database:**
```bash
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/dbname"
python scripts/seed_cat_items.py
```

#### Output Example
```
🌱 DreamSeed CAT Item Seeding Script
================================================================================

Database: postgresql+psycopg://postgres:***@127.0.0.1:5432/dreamseed_dev
Target: 120 items (40 per subject)
IRT Params: a=[0.8, 2.0], b=[-2.5, 2.5], c=[0.15, 0.25]

🎯 Subject: Mathematics
✅ Created item pool: Mathematics CAT Pool (ID: 1)
  Generated 10/40 items for math...
  Generated 20/40 items for math...
  Generated 30/40 items for math...
  Generated 40/40 items for math...

📊 IRT Statistics for MATH:
  Discrimination (a): min=0.812, max=1.987, mean=1.402
  Difficulty (b):     min=-2.301, max=2.487, mean=0.053
  Guessing (c):       min=0.152, max=0.248, mean=0.201
  Difficulty Distribution: Easy=9, Medium=22, Hard=9

✅ SEED DATA GENERATION COMPLETE
================================================================================

📈 Summary:
  Total Items Created: 120
  Item Pools: 3
  Subjects: math, english, science

✨ Ready for CAT engine testing!
```

#### Verification

**Check database:**
```bash
# Total items
psql -d dreamseed_dev -c "SELECT COUNT(*) FROM items;"

# Items by subject
psql -d dreamseed_dev -c "
  SELECT 
    meta->>'subject' as subject,
    COUNT(*) as count,
    ROUND(AVG(CAST(b AS FLOAT)), 2) as avg_difficulty
  FROM items 
  GROUP BY meta->>'subject';"

# Difficulty distribution
psql -d dreamseed_dev -c "
  SELECT 
    CASE 
      WHEN CAST(b AS FLOAT) < -1 THEN 'easy'
      WHEN CAST(b AS FLOAT) <= 1 THEN 'medium'
      ELSE 'hard'
    END as difficulty,
    COUNT(*) as count
  FROM items 
  GROUP BY difficulty
  ORDER BY difficulty;"
```

#### Next Steps

After seeding:

1. **Run E2E tests:**
   ```bash
   cd backend
   pytest tests/test_adaptive_exam_e2e.py -v
   ```

2. **Start API server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

3. **Test CAT flow:**
   ```bash
   # Start exam
   curl -X POST http://localhost:8000/api/adaptive/start \
     -H "Content-Type: application/json" \
     -d '{"exam_type": "placement"}'
   ```

#### Troubleshooting

**"Database not found":**
```bash
# Create database
createdb dreamseed_dev

# Run migrations
cd backend
alembic upgrade head
```

**"Items already exist":**
The script will prompt before adding duplicate data. To reset:
```bash
# Clear items (WARNING: deletes all items)
psql -d dreamseed_dev -c "TRUNCATE items CASCADE;"
```

**Import errors:**
Make sure you're running from the project root with venv activated:
```bash
cd /path/to/dreamseed_monorepo
source .venv/bin/activate
python scripts/seed_cat_items.py
```

---

## Additional Scripts

### `seed_users.py` (TODO)
Generate test users (students, teachers, parents)

### `seed_exam_sessions.py` (TODO)
Generate historical exam sessions with responses

### `seed_full_environment.py` (TODO)
One-command full database seeding (users + items + sessions)
