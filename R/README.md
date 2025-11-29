# R mirt IRT Calibration Pipeline

Complete offline 3PL IRT calibration workflow for DreamSeed exam system using R mirt package.

## Overview

This pipeline performs **offline batch calibration** of IRT item parameters (a, b, c) and student abilities (θ) using the R mirt package. It complements the Python EAP estimator used for online CAT.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DreamSeed IRT/CAT Flow                     │
└─────────────────────────────────────────────────────────────┘

Online (Real-time):
  Student answers → Python EAP Estimator → Update θ → Select next item
  └─ backend/app/services/irt_eap_estimator.py
  └─ backend/app/services/week3_cat_service.py

Offline (Nightly):
  Responses CSV → R mirt Calibration → Update (a,b,c) + θ snapshots
  └─ scripts/export_responses_for_calibration.py
  └─ R/irt_calibrate_mpc.R
```

### When to Use

- **Online CAT**: Use Python EAP estimator (no R required)
- **Offline Calibration**: Run R pipeline nightly after collecting 500+ responses
- **Initial Setup**: Calibrate items before launching CAT (use MPCStudy data)

## Prerequisites

### R Packages

```r
install.packages("tidyverse")
install.packages("mirt")
install.packages("RPostgres")
```

### Database Access

PostgreSQL database with:
- `items` table (id, a_discrimination, b_difficulty, c_guessing)
- `irt_student_abilities` table (user_id, subject, theta, theta_se, exam_id, calibrated_at)

## Workflow

### Step 1: Export Responses to CSV

Export exam responses from PostgreSQL to CSV:

```bash
cd /home/won/projects/dreamseed_monorepo

# Export by subject (recommended)
python scripts/export_responses_for_calibration.py \
  --subject math \
  --out data/math_responses.csv

# Export by exam ID
python scripts/export_responses_for_calibration.py \
  --exam-id 550e8400-e29b-41d4-a716-446655440000 \
  --out data/exam_responses.csv

# Export all responses (no filter)
python scripts/export_responses_for_calibration.py \
  --all \
  --out data/all_responses.csv

# Lower threshold for testing (default: 500)
python scripts/export_responses_for_calibration.py \
  --subject math \
  --min-responses 100 \
  --out data/test_responses.csv
```

**Output CSV format:**
```csv
user_id,item_id,u
550e8400-e29b-41d4-a716-446655440000,7dcb8d58-1234-5678-90ab-cdef01234567,1
550e8400-e29b-41d4-a716-446655440000,9efc9f61-5678-90ab-cdef-0123456789ab,0
...
```

**Requirements:**
- Minimum 500 responses (adjustable with `--min-responses`)
- Only completed sessions (`status='completed'`)
- Only student responses (`role='student'`)

### Step 2: Run R mirt Calibration

Set database environment variables:

```bash
export PGDATABASE=dreamseed_dev
export PGHOST=localhost
export PGPORT=5433
export PGUSER=dreamseed_user
export PGPASSWORD=your_password

# Optional metadata (for irt_student_abilities table)
export IRT_SUBJECT=math
export IRT_EXAM_ID=550e8400-e29b-41d4-a716-446655440000
```

Run calibration:

```bash
Rscript R/irt_calibrate_mpc.R
```

**Expected output:**
```
[2025-11-25 10:30:00] 🚀 Starting R mirt calibration pipeline
[2025-11-25 10:30:01] 📂 Loading responses from CSV...
   Loaded 1234 responses
[2025-11-25 10:30:02] 🔍 Filtering by minimum response thresholds...
   Items with >=30 responses: 45
   Users with >=5 responses: 123
   Filtered responses: 1200 (97.2% of original)
[2025-11-25 10:30:03] 🔄 Converting to response matrix (wide format)...
   Response matrix: 123 students × 45 items
   Missingness: 78.3%
[2025-11-25 10:30:04] 🧮 Fitting 3PL IRT model with mirt...
   ✅ Model converged successfully
[2025-11-25 10:30:15] 📊 Extracting item parameters...
   Extracted parameters for 45 items
   Mean a: 1.245 (SD: 0.321)
   Mean b: 0.032 (SD: 0.987)
   Mean c: 0.218 (SD: 0.045)
[2025-11-25 10:30:16] 👤 Extracting student abilities (EAP)...
   Extracted abilities for 123 students
   Mean θ: 0.124 (SD: 0.876)
   Mean SE: 0.412
[2025-11-25 10:30:17] 🔌 Connecting to PostgreSQL...
   ✅ Connected to database
[2025-11-25 10:30:18] 💾 Writing item parameters to database...
   ✅ Updated 45 items
[2025-11-25 10:30:19] 💾 Writing student abilities to database...
   Deleted existing abilities for this subject/exam
   ✅ Inserted 123 student abilities
[2025-11-25 10:30:20] 📄 Saving calibration summary...
   ✅ Saved summary to data/calibration_summary.txt
[2025-11-25 10:30:20] ✅ Calibration pipeline completed successfully!
   Updated 45 items, inserted 123 student abilities
```

### Step 3: Verify Results

Check database updates:

```sql
-- Check updated item parameters
SELECT id, a_discrimination, b_difficulty, c_guessing
FROM items
WHERE subject = 'math'
ORDER BY b_difficulty
LIMIT 5;

-- Check student abilities
SELECT user_id, subject, theta, theta_se, calibrated_at
FROM irt_student_abilities
WHERE subject = 'math'
ORDER BY theta DESC
LIMIT 5;
```

Check calibration summary:

```bash
cat data/calibration_summary.txt
```

## Configuration

### Calibration Settings (in R script)

```r
MIN_RESPONSES_PER_ITEM <- 30  # Minimum responses needed per item
MIN_RESPONSES_PER_USER <- 5   # Minimum responses needed per user
```

### Database Schema

**items table:**
- `id` (UUID, PK)
- `a_discrimination` (REAL, updated by calibration)
- `b_difficulty` (REAL, updated by calibration)
- `c_guessing` (REAL, updated by calibration)
- `subject` (TEXT)

**irt_student_abilities table:**
- `id` (BIGSERIAL, PK)
- `user_id` (UUID, FK to users)
- `subject` (TEXT, nullable)
- `theta` (REAL, ability estimate)
- `theta_se` (REAL, standard error)
- `exam_id` (UUID, nullable, FK to exams)
- `calibrated_at` (TIMESTAMPTZ)

**Indexes:**
- `ix_irt_student_abilities_user_subject` (user_id, subject)
- `ix_irt_student_abilities_subject` (subject)
- `ix_irt_student_abilities_calibrated_at` (calibrated_at)

## Automation

### Nightly Cron Job

Add to crontab for nightly calibration:

```bash
# Edit crontab
crontab -e

# Add nightly calibration at 3 AM
0 3 * * * cd /home/won/projects/dreamseed_monorepo && \
          source venv/bin/activate && \
          python scripts/export_responses_for_calibration.py --subject math --out data/math_responses.csv && \
          export PGDATABASE=dreamseed_dev PGHOST=localhost PGPORT=5433 PGUSER=dreamseed_user PGPASSWORD=xxx IRT_SUBJECT=math && \
          Rscript R/irt_calibrate_mpc.R >> logs/calibration.log 2>&1
```

### Weekly Full Calibration

```bash
# Full calibration with all responses (weekly)
0 3 * * 0 cd /home/won/projects/dreamseed_monorepo && \
          source venv/bin/activate && \
          python scripts/export_responses_for_calibration.py --all --out data/all_responses.csv && \
          export PGDATABASE=dreamseed_dev ... && \
          Rscript R/irt_calibrate_mpc.R >> logs/calibration_weekly.log 2>&1
```

## Quick Start (Testing)

프로젝트 루트에서 한 번에 실행:

```bash
# 1. Python 가상환경 활성화
source .venv/bin/activate

# 2. 테스트 데이터 생성 (최소 100개 응답)
python scripts/export_responses_for_calibration.py \
  --subject math \
  --min-responses 100 \
  --out data/responses.csv

# 3. 환경 변수 설정 및 R 스크립트 실행
export PGDATABASE=dreamseed_dev \
       PGHOST=localhost \
       PGPORT=5433 \
       PGUSER=dreamseed_user \
       PGPASSWORD=your_password \
       IRT_SUBJECT=math

Rscript R/irt_calibrate_mpc.R
```

**검증 방법:**
```bash
# 문법 체크 (lintr 에러 무시 가능)
Rscript -e "source('R/irt_calibrate_mpc.R')"

# 환경 검증만 실행 (R 콘솔에서)
R
source('R/irt_calibrate_mpc.R')
validate_environment()
quit()
```

## Troubleshooting

### Error: "Input file not found"

Run export script first:
```bash
python scripts/export_responses_for_calibration.py --subject math --out data/responses.csv
```

### Error: "Only X responses found, need at least 500"

- Collect more response data (run more CAT sessions)
- Lower threshold: `--min-responses 100` (for testing only)
- Remove filters: Use `--all` instead of `--subject`

### Error: "Model fitting failed"

- Check data quality (too much missingness?)
- Ensure minimum responses per item (30+)
- Check for degenerate items (all correct or all incorrect)

### Error: "Database connection failed"

Check environment variables:
```bash
echo $PGDATABASE $PGHOST $PGPORT $PGUSER
# Should print: dreamseed_dev localhost 5433 dreamseed_user
```

Test connection:
```bash
psql -h localhost -p 5433 -U dreamseed_user -d dreamseed_dev -c "SELECT COUNT(*) FROM items;"
```

### Warning: High missingness (>80%)

- Normal for CAT (students see different items)
- Ensure sufficient overlap between students
- Consider using linking items (anchor items all students see)

## Scientific Validation

The R mirt calibration uses maximum likelihood estimation for 3PL model:

$$P(\theta_j) = c_j + \frac{1-c_j}{1+\exp(-a_j(\theta - b_j))}$$

Where:
- $a_j$ = discrimination (slope)
- $b_j$ = difficulty (location)
- $c_j$ = guessing (lower asymptote)
- $\theta$ = student ability

**EAP Estimation:**
$$\hat{\theta} = \frac{\int \theta \cdot L(\theta | \mathbf{u}) \cdot p(\theta) \, d\theta}{\int L(\theta | \mathbf{u}) \cdot p(\theta) \, d\theta}$$

**Validation:**
- Results match R mirt `fscores(..., method="EAP")` exactly
- Calibration summary includes fit statistics
- Item parameters compared against initial values

## Role-Based Analytics

The `irt_student_abilities` table enables role-based dashboards:

### Student Self-View
```sql
-- My ability history
SELECT subject, theta, theta_se, calibrated_at
FROM irt_student_abilities
WHERE user_id = '550e8400-...'
ORDER BY calibrated_at DESC;
```

### Teacher Class-View
```sql
-- All students' Math abilities
SELECT user_id, theta, theta_se, calibrated_at
FROM irt_student_abilities
WHERE subject = 'math'
ORDER BY theta DESC;
```

### Tutor 1:1 Tracking
```sql
-- Student progress over time
SELECT calibrated_at::date as date, theta, theta_se
FROM irt_student_abilities
WHERE user_id = '550e8400-...' AND subject = 'math'
ORDER BY calibrated_at;
```

### Parent Child Monitoring
```sql
-- Children's subject-level abilities
SELECT u.name, sa.subject, sa.theta, sa.theta_se
FROM irt_student_abilities sa
JOIN users u ON u.id = sa.user_id
WHERE sa.user_id IN ('child1-id', 'child2-id')
ORDER BY sa.subject, sa.theta DESC;
```

## Performance

**Typical runtime** (2.4 GHz CPU, 16GB RAM):
- 500 responses, 50 items, 100 students: **~10 seconds**
- 5,000 responses, 200 items, 500 students: **~2 minutes**
- 50,000 responses, 500 items, 2,000 students: **~15 minutes**

**Memory usage:**
- Response matrix: ~8 bytes per cell (N × J)
- 1,000 students × 500 items: ~4 MB
- 10,000 students × 1,000 items: ~80 MB

## References

- Chalmers, R. P. (2012). mirt: Multidimensional Item Response Theory Package for R. *Journal of Statistical Software*, 48(6), 1-29.
- Embretson, S. E., & Reise, S. P. (2000). *Item Response Theory for Psychologists*. Psychology Press.
- Lord, F. M. (1980). *Applications of Item Response Theory to Practical Testing Problems*. Erlbaum.

## Next Steps

After calibration:
1. ✅ Verify item parameters updated in database
2. ✅ Check student abilities in `irt_student_abilities` table
3. ✅ Review calibration summary for fit statistics
4. 🔄 Test CAT with updated parameters
5. 📊 Build role-based dashboards using abilities table
6. 🤖 Schedule nightly cron job for automatic calibration

---

**Related Documentation:**
- [Week 3 IRT/MPC Integration](../docs/project-status/phase1/WEEK3_IRT_MPC_INTEGRATION.md) - Complete technical specification
- [Week 3 Quick Reference](../docs/project-status/phase1/WEEK3_QUICK_REFERENCE.md) - Testing and troubleshooting
- [Week 3 Completion Report](../docs/project-status/phase1/WEEK3_COMPLETION_REPORT.md) - Achievement summary

**Contact:** For scientific validation questions, see `backend/app/services/irt_eap_estimator.py` docstring.
