# Week 3 Integration - Quick Reference

**TL;DR**: Week 3 backend now integrates mirt-aligned IRT/CAT with MPCStudy question bank migration.

---

## 🚀 Quick Start

### 1. Run Database Migration

```bash
cd /home/won/projects/dreamseed_monorepo/backend

# Option A: Alembic (if env.py configured)
alembic upgrade head

# Option B: Manual script
python scripts/create_week3_tables.py
```

### 2. Migrate MPCStudy Questions

```bash
# Set MySQL connection
export MPC_MYSQL_URL="mysql://user:pass@localhost/mpc_db"

# Dry run (preview only)
python scripts/migrate_mpc_to_dreamseed.py --subject math --dry-run

# Real migration
python scripts/migrate_mpc_to_dreamseed.py --subject math --batch-size 50 --create-exam
```

### 3. Test CAT Engine

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8001

# Test sequence (see full curl commands in WEEK3_IRT_MPC_INTEGRATION.md)
# 1. Login → TOKEN
# 2. GET /api/exams/{exam_id} → Verify exam
# 3. POST /api/exams/{exam_id}/sessions → SESSION_ID
# 4. Loop: GET current-question → POST answer (theta updates!)
# 5. GET summary → Final results
```

---

## 📁 Files Created

### Core IRT Engine
- `backend/app/services/irt_eap_estimator.py` - **mirt-aligned EAP theta estimation**
  - `update_theta_eap()` - Main function (compatible with R mirt)
  - `irt_prob_3pl()` - 3PL probability function
  - `irt_information_3pl()` - Fisher information
  - Score conversion utilities

### MPCStudy Migration
- `backend/app/services/wiris_converter.py` - **Wiris → MathLive conversion**
  - `mathml_to_latex()` - MathML parser
  - `convert_wiris_html_to_mathlive()` - Full HTML pipeline
  - `estimate_initial_irt_params()` - Difficulty (1-5) → IRT (a,b,c)

- `scripts/migrate_mpc_to_dreamseed.py` - **ETL script**
  - MySQL → PostgreSQL migration
  - Automatic exam creation
  - Traceability via `mpc_item_mapping` table

### Database Schema
- `backend/alembic/versions/2025_11_25_01_week3_exam_models.py` - **Alembic migration**
  - 7 tables with UUID primary keys
  - IRT 3PL parameters (a, b, c)
  - CAT state tracking (theta, theta_se)

### Documentation
- `docs/project-status/phase1/WEEK3_IRT_MPC_INTEGRATION.md` - **Complete technical guide**
- `docs/project-status/phase1/WEEK3_QUICK_REFERENCE.md` - **This file**

---

## 🔬 Key Concepts

### IRT 3PL Model

```
P(θ) = c + (1 - c) / (1 + exp(-a * (θ - b)))

a = discrimination (0.5 - 2.5)
b = difficulty (-3 to +3)
c = guessing (0.15 - 0.25 for 4-choice)
θ = ability estimate
```

### EAP Theta Estimation

**Online CAT** (Python):
```python
responses = [(a, b, c, u), ...]  # Full history
theta, se = update_theta_eap(responses)
```

**Offline Calibration** (R mirt):
```r
mod <- mirt(data, 1, itemtype = "3PL")
theta <- fscores(mod, method = "EAP")
```

Both methods should produce **theta within 0.05** for same response pattern.

### CAT Termination Criteria

1. **SE Convergence**: `theta_se < 0.3` (reliable estimate)
2. **Max Questions**: `questions_answered >= max_questions` (e.g., 20)
3. **Time Limit**: `current_time >= ends_at`

---

## 🧪 Testing

### Unit Tests (Recommended)

```bash
cd backend
pytest tests/test_irt_eap_estimator.py -v
pytest tests/test_wiris_converter.py -v
```

### Manual API Test

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -d "username=student4@dreamseed.ai&password=TestPass123!" | jq -r .access_token)

# 2. Get exam
EXAM_ID="<from migration output>"
curl -X GET "http://localhost:8001/api/exams/$EXAM_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Start session
SESSION_ID=$(curl -s -X POST "http://localhost:8001/api/exams/$EXAM_ID/sessions" \
  -H "Authorization: Bearer $TOKEN" | jq -r .id)

# 4. Get first question
curl -X GET "http://localhost:8001/api/exam-sessions/$SESSION_ID/current-question" \
  -H "Authorization: Bearer $TOKEN" | jq

# 5. Submit answer (get QUESTION_ID and OPTION_ID from step 4)
curl -X POST "http://localhost:8001/api/exam-sessions/$SESSION_ID/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"questionId":"...","selectedOptionId":"...","timeSpentSeconds":45}' | jq

# 6. Repeat steps 4-5 until "no_more_questions"

# 7. Get results
curl -X GET "http://localhost:8001/api/exam-sessions/$SESSION_ID/summary" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 📊 Expected Theta Trajectory

Typical CAT session with 10 questions:

```
Question 1: θ = 0.000, SE = 1.000 (prior)
Question 2: θ = 0.523, SE = 0.654 (first update)
Question 3: θ = 0.812, SE = 0.421 (converging)
Question 4: θ = 0.431, SE = 0.318 (more stable)
Question 5: θ = 0.678, SE = 0.265 ✓ SE < 0.3 (can terminate)
```

**Good Signs**:
- Theta moves in response to correct/incorrect answers
- SE decreases monotonically
- SE < 0.3 within 5-10 questions

**Bad Signs**:
- Theta stuck at 0.0 → Items not discriminating
- SE not decreasing → Check item information function
- SE oscillating → Numerical instability (check overflow protection)

---

## 🐛 Troubleshooting

### Migration Fails: "MathML conversion error"

**Symptom**: Some questions have `[MATH_ERROR]` in stem_html

**Solution**:
1. Check Wiris HTML format in MPCStudy
2. May need WIRIS official converter API
3. For now, manually fix problematic questions:
   ```sql
   UPDATE items SET stem_html = '...' WHERE stem_html LIKE '%[MATH_ERROR]%';
   ```

### Theta Not Updating

**Symptom**: Theta stays at 0.0 after multiple responses

**Debug**:
```python
# Check if update_theta_eap is being called
# Add logging in week3_cat_service.py
import logging
logger.info(f"Updating theta: responses={len(response_list)}, theta_before={theta_before}")

# Check if responses are loaded
logger.info(f"Response list: {response_list}")
```

**Common causes**:
- `responses` not loaded with `selectinload(ExamSessionResponse.item)`
- IRT parameters all zeros (check seed data)

### SE Not Converging

**Symptom**: SE stays > 0.5 after 20 questions

**Check**:
1. Item discrimination (a): Should be 0.8 - 2.0
2. Item difficulty spread: Need items at different b values
3. Guessing parameter: Should be < 0.3

```sql
-- Check item parameter distribution
SELECT 
  AVG(a_discrimination) as avg_a,
  MIN(b_difficulty) as min_b,
  MAX(b_difficulty) as max_b,
  AVG(c_guessing) as avg_c
FROM items WHERE subject = 'math';

-- Expected:
-- avg_a: 1.0 - 1.5
-- min_b: -2.0 or lower
-- max_b: +2.0 or higher
-- avg_c: 0.15 - 0.25
```

---

## 📈 Performance Tips

### 1. Database Indexes

Already created in migration:
```sql
-- These are critical for CAT performance
CREATE INDEX ix_items_subject_active ON items (subject, is_active);
CREATE INDEX ix_items_difficulty ON items (b_difficulty);
CREATE INDEX ix_exam_sessions_user_status ON exam_sessions (user_id, status);
```

### 2. Query Optimization

Use `selectinload` for eager loading:
```python
# Good (1 query)
await db.execute(
    select(ExamSessionResponse)
    .options(selectinload(ExamSessionResponse.item))
)

# Bad (N+1 queries)
responses = await db.execute(select(ExamSessionResponse))
for resp in responses:
    item = await db.get(Item, resp.item_id)  # Extra query!
```

### 3. EAP Grid Resolution

Default: 81 points (theta = -4 to +4, step 0.1)

For faster CAT (if needed):
```python
theta, se = update_theta_eap(
    responses,
    theta_grid_step=0.2  # 41 points instead of 81
)
# Speed: 2x faster, accuracy: ±0.02 theta
```

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Run Alembic migration on staging
- [ ] Migrate sample MPCStudy data (50 questions)
- [ ] Create 3 test exams (Math, English, Science)
- [ ] Manual test: Complete 1 exam from start to finish
- [ ] Verify theta trajectory makes sense
- [ ] Check API response times (< 200ms)
- [ ] Monitor database query performance
- [ ] Set up error tracking (Sentry)
- [ ] Document any WIRIS conversion issues
- [ ] Plan R mirt calibration after collecting 500+ responses

---

## 🔗 Related Documentation

- **Week 3 Backend**: `docs/project-status/phase1/WEEK3_BACKEND_COMPLETE.md`
- **IRT/CAT Technical**: `docs/project-status/phase1/WEEK3_IRT_MPC_INTEGRATION.md`
- **API Contract**: `docs/project-status/phase1/PHASE1_API_CONTRACT.md`
- **Phase 1 Status**: `docs/project-status/phase1/PHASE1_STATUS.md`

---

## 💬 Questions?

**Common Questions**:

**Q: Why EAP instead of Newton-Raphson MLE?**  
A: EAP is more stable for short tests (< 20 items) and handles extreme theta values better. MLE can diverge with perfect scores.

**Q: When do we recalibrate IRT parameters?**  
A: After collecting 500+ student responses. Use R mirt offline:
```r
mod <- mirt(response_matrix, 1, itemtype = "3PL")
pars <- coef(mod, IRTpars = TRUE, simplify = TRUE)$items
# Update database with new (a, b, c)
```

**Q: Can we use 2PL or 1PL instead of 3PL?**  
A: Yes! Set `c_guessing = 0.0` for 2PL. For 1PL (Rasch), set both `a_discrimination = 1.0` and `c_guessing = 0.0`.

**Q: How to handle non-MCQ items (short answer, essay)?**  
A: For Phase 1A, only MCQ supported. Phase 2 will add:
- Partial credit items (GPCM model)
- Constructed response (manual scoring + IRT)

---

**Last Updated**: November 25, 2025  
**Version**: 1.0  
**Status**: ✅ Ready for Testing
