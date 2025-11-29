# Student Emotive Dashboard - Complete Package

**Student-facing emotive dashboard** with mood tracking, AI encouragement, and goal management.

## 📋 Overview

A warm, supportive dashboard that helps students:
- 📊 Track learning progress (7-day growth rate)
- 😊 Log daily mood (happy/neutral/sad)
- 🎯 Set and complete learning goals
- 💬 Receive AI-generated encouragement
- 🔥 Maintain learning streaks

**Multitenancy:** All data scoped by `tenant_id` + `student_id`  
**RBAC:** Requires `student` role (admins also allowed)  
**ID Type:** TEXT-based IDs (not UUID)

## 📦 Package Contents

```
apps/seedtest_api/
├── models/
│   └── student_emotive.py                  # 4 tables (mood, log, goal, ai_message)
├── routers/
│   └── student_dashboard.py                # 5 endpoints (dashboard, mood, goals)
├── services/
│   └── ai_empathy.py                       # Rule-based AI message generator
└── alembic/versions/
    └── 20251107_1100_student_emotive.py    # Migration

scripts/seed/
└── seed_student_emotive.py                 # Sample data generator

docs/student_dashboard/
└── README.md                               # This file
```

## 🗄️ Database Tables

### 1. `student_mood`
Daily mood tracking with optional notes.

```sql
CREATE TABLE student_mood (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    day DATE NOT NULL,
    mood VARCHAR(8) NOT NULL,  -- 'happy' | 'neutral' | 'sad'
    note VARCHAR(512),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, student_id, day)
);
```

### 2. `student_daily_log`
Quantitative learning metrics per day.

```sql
CREATE TABLE student_daily_log (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    day DATE NOT NULL,
    study_minutes INT DEFAULT 0,
    tasks_done INT DEFAULT 0,
    theta_delta FLOAT DEFAULT 0.0,  -- IRT ability change
    reflections VARCHAR(1000),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, student_id, day)
);
```

### 3. `student_goal`
Personal learning goals.

```sql
CREATE TABLE student_goal (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    title VARCHAR(200) NOT NULL,
    target_date DATE,
    done BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);
```

### 4. `student_ai_message`
Cached AI-generated encouragement messages.

```sql
CREATE TABLE student_ai_message (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    tenant_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    day DATE NOT NULL,
    message VARCHAR(1000) NOT NULL,
    tone VARCHAR(24) DEFAULT 'warm',  -- 'warm' | 'gentle' | 'energetic'
    meta JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, student_id, day)
);
```

## 🔌 API Endpoints

All endpoints require:
- **JWT Authentication**: `Authorization: Bearer <token>`
- **Role**: `student` or `admin`
- **Scoping**: Automatically filtered by `tenant_id` + `student_id` from JWT

### GET `/api/student/dashboard`

Main dashboard data.

**Response:**
```json
{
  "week_growth": 0.035,
  "today_mood": "happy",
  "streak_days": 5,
  "goals": [
    {
      "id": "goal-abc-123",
      "title": "인수분해 3문제 풀기",
      "target_date": "2025-11-10",
      "done": false
    }
  ],
  "ai_message": "이번 주 +0.04만큼 성장했어요! 꾸준함이 빛나요 ✨ 🔥 5일 연속 학습! 대단해요!",
  "ai_tone": "energetic"
}
```

### POST `/api/student/mood`

Set today's mood.

**Request:**
```json
{
  "mood": "happy",
  "note": "오늘 문제 잘 풀렸어요!"
}
```

**Response:**
```json
{
  "ok": true,
  "mood": "happy"
}
```

### POST `/api/student/goals`

Create new goal.

**Request:**
```json
{
  "title": "이차방정식 복습하기",
  "target_date": "2025-11-15"
}
```

**Response:**
```json
{
  "id": "goal-xyz-789",
  "title": "이차방정식 복습하기"
}
```

### POST `/api/student/goals/{goal_id}/done`

Mark goal as complete.

**Response:**
```json
{
  "ok": true,
  "goal_id": "goal-xyz-789"
}
```

### DELETE `/api/student/goals/{goal_id}`

Delete goal.

**Response:**
```json
{
  "ok": true,
  "deleted_id": "goal-xyz-789"
}
```

## 🚀 Deployment

### 1. Run Migration

```bash
cd /home/won/projects/dreamseed_monorepo
alembic upgrade head
```

### 2. Register Router

Add to `apps/seedtest_api/main.py`:

```python
from apps.seedtest_api.routers import student_dashboard

app.include_router(student_dashboard.router)
```

### 3. Seed Sample Data (Optional)

```bash
python -m scripts.seed.seed_student_emotive \
  --tenant org-dreamseed-001 \
  --student student-alice-001 \
  --days 10
```

### 4. Test with JWT

Generate JWT with:
```json
{
  "sub": "student-alice-001",
  "tenant_id": "org-dreamseed-001",
  "roles": ["student"]
}
```

Test endpoint:
```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/student/dashboard
```

## 🎨 AI Message Engine

Current implementation is **rule-based** (see `services/ai_empathy.py`):

```python
def make_message(theta_delta_7d: float, mood: str | None, streak_days: int) -> Message:
    """Generate encouragement based on:
    - theta_delta_7d: Performance trend (IRT)
    - mood: Current emotional state
    - streak_days: Consistency metric
    
    Returns: Message(text, tone, context)
    """
```

**Message templates:**
- Strong growth (>0.05): "이번 주 +X만큼 성장했어요! 꾸준함이 빛나요 ✨"
- Steady growth: "꾸준한 리듬이 좋아요. 오늘도 20분만 집중해볼까요? 💪"
- Slight decline: "괜찮아요. 오늘은 가벼운 문제부터 다시 시작해봐요 🌱"

**Mood adjustments:**
- `sad` → Always gentle tone + comfort message
- `happy` → Energetic tone boost
- `neutral` → No modification

**Streak bonuses:**
- 7+ days: "🔥 X일 연속 학습! 대단해요!"
- 3-6 days: "💪 X일 연속! 이 리듬 좋아요."

### Future: LLM Integration

Replace `make_message()` with LLM call:

```python
from openai import OpenAI

def make_message_llm(theta_delta_7d, mood, streak_days):
    client = OpenAI()
    prompt = f"""You are a warm, encouraging Korean tutor.
    Student's 7-day growth: {theta_delta_7d:+.2f}
    Current mood: {mood}
    Streak: {streak_days} days
    
    Generate a short, emotive encouragement message (max 100 chars).
    Tone: {'gentle' if mood == 'sad' else 'energetic' if theta_delta_7d > 0.05 else 'warm'}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    return Message(text=response.choices[0].message.content, ...)
```

## 📊 Data Flow

```
1. Student logs mood
   POST /api/student/mood → StudentMood table

2. System tracks daily activity
   Backend job → StudentDailyLog (study_minutes, theta_delta)

3. Student visits dashboard
   GET /api/student/dashboard
   ├─ Query StudentDailyLog (7d average)
   ├─ Query StudentMood (today)
   ├─ Calculate streak
   ├─ Query StudentGoal (active only)
   └─ Check StudentAIMessage cache
       └─ If not cached → Generate → Cache → Return

4. Student creates goals
   POST /api/student/goals → StudentGoal table

5. Student completes goal
   POST /api/student/goals/{id}/done → Update StudentGoal.done
```

## 🔒 Security

- **Authentication**: JWT Bearer token required
- **Authorization**: `require_role("student")` decorator
- **Tenant Isolation**: All queries automatically scoped by `tenant_id`
- **Student Isolation**: All queries scoped by `student_id` from JWT
- **Input Validation**: Pydantic models with length/pattern constraints

## 🧪 Testing

### Unit Tests

```python
# Test AI message generation
from apps.seedtest_api.services.ai_empathy import make_message

def test_strong_growth_message():
    msg = make_message(theta_delta_7d=0.08, mood='happy', streak_days=5)
    assert '+0.08' in msg.text
    assert msg.tone == 'energetic'
    assert '5일 연속' in msg.text

def test_sad_mood_override():
    msg = make_message(theta_delta_7d=0.08, mood='sad', streak_days=0)
    assert msg.tone == 'gentle'  # Overrides energetic
```

### Integration Tests

```python
def test_dashboard_endpoint(client, student_jwt):
    response = client.get(
        '/api/student/dashboard',
        headers={'Authorization': f'Bearer {student_jwt}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'week_growth' in data
    assert 'ai_message' in data
```

## 📈 Performance Considerations

- **AI Message Caching**: One message per student per day (reduces LLM API calls)
- **Indexes**: Composite indexes on `(tenant_id, student_id, day)` for all tables
- **Streak Calculation**: Limited to last 30 days (prevents full table scan)
- **Goal Query**: Limit 5 active goals (prevents unbounded results)

## 🎯 Next Steps

1. **Frontend Integration**
   - React/Vue component for student dashboard
   - Mood emoji selector UI
   - Goal management interface
   - AI message display with tone-based styling

2. **Advanced Features**
   - Weekly/monthly reports
   - Peer comparison (anonymized)
   - Badge/achievement system
   - Notification system (reminders, encouragement)

3. **AI Enhancements**
   - LLM integration (GPT-4, Claude)
   - Personalized message history learning
   - Multi-language support
   - Voice message option

4. **Analytics**
   - Teacher view of student mood trends
   - Correlation between mood and performance
   - Early intervention alerts (sustained low mood)

## 📝 License

Part of DreamSeed Teacher Dashboard (Multitenant + RBAC) package.

---

**Created:** 2025-11-07  
**Version:** 1.0.0  
**Maintainer:** DreamSeed AI Team
