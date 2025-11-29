# Phase 2 Master Plan - Combined Academic & Aptitude Platform

**Date:** November 24, 2025  
**Status:** 📋 Planning Complete  
**Implementation:** Phase 2.0 (Q1 2026)  

---

## 🎯 Vision: DreamSeed AI = Academic + Aptitude

### The Complete Platform

```
┌─────────────────────────────────────────────────────────────────┐
│                     DreamSeed AI Platform                       │
│                  "Know Yourself, Choose Wisely"                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🧮 Pillar 1: Academic Achievement Assessment                  │
│     ├─ CAT/IRT Adaptive Testing                                │
│     ├─ Math, English, Science                                  │
│     ├─ Ability estimation (θ)                                  │
│     ├─ Diagnostic feedback                                     │
│     └─ Phase 1.0 ✅ COMPLETE                                    │
│                                                                 │
│  🎨 Pillar 2: Aptitude & Interest Profiling                    │
│     ├─ Career/Major Guidance                                   │
│     ├─ STEM vs Humanities vs Arts                              │
│     ├─ Learning style assessment                               │
│     ├─ Interest/personality dimensions                         │
│     └─ Phase 2.0 ⏸️ PLANNED                                     │
│                                                                 │
│  🤝 Integration: Combined Insights                             │
│     ├─ Academic ability + Aptitude profile                     │
│     ├─ Personalized major recommendations                      │
│     ├─ Career path suggestions                                 │
│     ├─ Study strategy optimization                             │
│     └─ Phase 2.5 🔮 FUTURE                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Why Two Pillars Matter

### Problem Statement

**Current EdTech Limitation:**
- Academic tests only measure **what students know**
- No guidance on **what students are good at**
- No insight into **what students enjoy**
- Result: Poor major/career decisions → Dropouts, career changes

**DreamSeed Solution:**
- Academic CAT → Objective ability measurement
- Aptitude Assessment → Interest & talent profiling
- Combined → **Data-driven personalized recommendations**

### Market Positioning

| Platform | Academic Testing | Aptitude Testing | Combined Insights |
|----------|------------------|------------------|-------------------|
| Khan Academy | ✅ | ❌ | ❌ |
| Duolingo | ✅ (Language) | ❌ | ❌ |
| College Board (SAT) | ✅ | ❌ | ❌ |
| Holland Code (Careers) | ❌ | ✅ | ❌ |
| **DreamSeed AI** | ✅ CAT/IRT | ✅ 6 Dimensions | ✅ **UNIQUE** |

**Competitive Advantage:** Only platform combining rigorous academic assessment with comprehensive aptitude profiling.

---

## 🗺️ Roadmap Overview

### Phase 1.0 (Nov 2025 - Dec 2025) ✅ COMPLETE
- Math CAT engine (3PL IRT)
- JWT authentication
- Student dashboard
- Basic exam flow
- dreamseedai.com deployment
- **Result:** Academic pillar foundation

### Phase 1.5 (Jan 2026 - Feb 2026) 🔄 NEXT
- English CAT
- Science CAT
- Multi-subject dashboard
- Comparative analytics
- **Result:** Academic pillar complete

### Phase 2.0 (Mar 2026 - Apr 2026) ⏸️ PLANNED
- Aptitude survey engine
- 6 dimension scoring
- Career fit algorithms
- Profile dashboard
- **Result:** Aptitude pillar launch

### Phase 2.5 (May 2026 - Jun 2026) 🔮 FUTURE
- Combined recommendation engine
- LLM-powered insights
- Parent/Teacher dashboards
- Advanced visualizations
- **Result:** Full platform integration

---

## 🧱 Phase 2.0 Technical Architecture

### Database Extensions

**New Tables (6):**
```
aptitude_surveys          - Survey definitions
aptitude_questions        - Question bank
aptitude_options          - Likert scale options
aptitude_sessions         - Student sessions
aptitude_responses        - Individual answers
aptitude_profiles         - Aggregated profiles
```

**Integration Points:**
- `students.id` → Foreign key in aptitude_profiles
- `users.id` → Session ownership
- Academic results (exam_sessions) + Aptitude profiles → Combined recommendations

### API Extensions

**New Namespace:** `/api/aptitude`

**Endpoints:**
- POST `/surveys/{id}/start` - Begin survey
- GET `/surveys/{id}/questions` - Fetch questions
- POST `/surveys/{id}/submit` - Submit responses
- GET `/results/{session_id}` - Get results
- GET `/profile` - Get student profile

### Frontend Components

**New Pages:**
- `/aptitude` - Survey landing
- `/aptitude/survey/{id}` - Question flow
- `/aptitude/results/{id}` - Results page
- `/profile` - Combined profile view

**New Components:**
- `<LikertQuestion>` - 5-point scale UI
- `<DimensionChart>` - Bar/radar visualization
- `<RecommendationCard>` - Major suggestions
- `<ProfileSummary>` - Overview widget

---

## 📐 Dimension Framework (6 Dimensions)

### Core Dimensions

| Dimension | Range | Description | Sample Question |
|-----------|-------|-------------|-----------------|
| **STEM_interest** | -1 to +1 | 이공계 흥미도 | "수학 문제를 푸는 것이 즐겁다" |
| **Verbal_aptitude** | -1 to +1 | 언어적 사고력 | "글쓰기로 생각을 표현하는 게 편하다" |
| **Artistic_creativity** | -1 to +1 | 예술적 창의성 | "새로운 디자인을 만드는 게 좋다" |
| **Social_orientation** | -1 to +1 | 사회적 지향성 | "사람들과 함께 일하는 게 좋다" |
| **Practical_hands_on** | -1 to +1 | 실무/실습 선호 | "실제로 만들어보는 활동이 좋다" |
| **Logical_reasoning** | -1 to +1 | 논리적 사고력 | "복잡한 문제를 분석하는 게 재미있다" |

### Career Fit Formulas

**Engineering:**
```
Engineering_fit = 0.40 × STEM + 0.30 × Logical + 0.20 × Practical - 0.10 × Social
```

**Computer Science:**
```
CS_fit = 0.50 × STEM + 0.40 × Logical + 0.10 × Practical
```

**Business:**
```
Business_fit = 0.40 × Verbal + 0.30 × Social + 0.20 × Logical + 0.10 × Practical
```

**Humanities:**
```
Humanities_fit = 0.50 × Verbal + 0.30 × Artistic + 0.20 × Social - 0.20 × STEM
```

**Arts:**
```
Arts_fit = 0.60 × Artistic + 0.30 × Verbal + 0.10 × Social
```

**Medicine:**
```
Medicine_fit = 0.30 × STEM + 0.25 × Logical + 0.25 × Practical + 0.20 × Social
```

---

## 🤝 Combined Insights (Phase 2.5)

### Integration Logic

```python
def generate_combined_recommendation(student_id):
    # Get academic data
    math_theta = get_theta(student_id, "math")
    english_theta = get_theta(student_id, "english")
    
    # Get aptitude data
    profile = get_aptitude_profile(student_id)
    stem = profile["STEM_interest"]
    verbal = profile["Verbal_aptitude"]
    
    # Combined scoring
    recommendations = []
    
    # High math + high STEM → Engineering/CS
    if math_theta > 1.0 and stem > 0.5:
        recommendations.append({
            "major": "Computer Science",
            "score": 0.95,
            "reason": "Strong math ability (θ=1.2) + High STEM interest (0.8)"
        })
    
    # High english + high verbal → Humanities/Law
    elif english_theta > 1.0 and verbal > 0.5:
        recommendations.append({
            "major": "Law / Political Science",
            "score": 0.90,
            "reason": "Excellent language ability (θ=1.3) + Strong verbal aptitude (0.7)"
        })
    
    # Balanced academic + high artistic → Architecture/Design
    elif abs(math_theta - english_theta) < 0.5 and profile["Artistic_creativity"] > 0.7:
        recommendations.append({
            "major": "Architecture / Industrial Design",
            "score": 0.88,
            "reason": "Balanced academic skills + High creativity (0.9)"
        })
    
    # ... more rules
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:3]
```

### Example Output

**Student Profile:**
- Math θ: 1.5 (Top 7%)
- English θ: 0.2 (Average)
- STEM Interest: 0.9
- Logical Reasoning: 1.2
- Practical Hands-on: 0.7

**Combined Recommendation:**
1. **Computer Science / AI** (Score: 0.95)
   - Strong math ability (θ=1.5, top 7%)
   - Exceptional STEM interest (0.9)
   - Outstanding logical reasoning (1.2)
   - Recommended courses: Data Structures, Machine Learning

2. **Electrical Engineering** (Score: 0.88)
   - Strong math + practical orientation
   - Engineering mindset
   - Recommended courses: Circuit Theory, Embedded Systems

3. **Applied Mathematics** (Score: 0.82)
   - Exceptional math ability
   - Logical reasoning strength
   - Recommended courses: Real Analysis, Optimization

---

## 📊 Success Metrics

### Phase 2.0 KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Survey Completion Rate | > 80% | % of students completing 30 questions |
| Average Survey Time | 12-18 min | Actual time from start to submit |
| Recommendation Accuracy | > 70% | Student agreement with top 3 majors |
| Profile Confidence Score | > 0.75 | System-calculated reliability |
| Beta Tester Satisfaction | > 4.0/5 | Survey feedback (1-5 scale) |

### Phase 2.5 KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Combined Recommendation Usage | > 60% | % viewing combined insights page |
| Parent Engagement | > 40% | % of parents accessing child's profile |
| Major Decision Confidence | > 4.2/5 | Student survey on decision clarity |
| Platform NPS | > 50 | Net Promoter Score |

---

## 🚀 Implementation Timeline

### Phase 2.0 Sprint Plan (8 weeks)

**Week 1-2: Backend Foundation**
- Database schema (6 tables)
- Alembic migration
- Seed 30-question survey
- API endpoints (5 routes)
- Unit tests

**Week 3-4: Scoring Engine**
- Dimension calculation
- Career fit algorithms
- Profile generation
- Integration tests

**Week 5-6: Frontend Development**
- Survey UI (Likert questions)
- Results page (visualizations)
- Profile dashboard
- E2E tests

**Week 7: Integration & Testing**
- API integration
- Performance testing
- Bug fixes
- Beta deployment

**Week 8: Beta Testing**
- 20-30 student pilot
- Feedback collection
- Refinements
- Production release

---

## 📄 Related Documentation

**Phase 1 Docs:**
- [PHASE1_API_CONTRACT.md](../phase1/PHASE1_API_CONTRACT.md) - Academic API spec
- [PHASE1_ALPHA_CHECKLIST.md](../phase1/PHASE1_ALPHA_CHECKLIST.md) - Alpha completion criteria
- [PHASE1_STATUS.md](../phase1/PHASE1_STATUS.md) - Current progress

**Phase 2 Docs:**
- [PHASE2_APTITUDE_ASSESSMENT.md](./PHASE2_APTITUDE_ASSESSMENT.md) - Complete aptitude spec
- [APTITUDE_SAMPLE_QUESTIONS.md](./APTITUDE_SAMPLE_QUESTIONS.md) - 30 sample questions
- [PHASE2_COMBINED_INSIGHTS.md](./PHASE2_COMBINED_INSIGHTS.md) - Integration strategy (TBD)

---

## 🎯 Next Actions

### Immediate (Post Phase 1.0):
- [ ] Review Phase 2.0 specification with stakeholders
- [ ] Finalize dimension framework
- [ ] Create full 30-question survey content
- [ ] Design frontend mockups

### Week 1 (Phase 2.0 Start):
- [ ] Create Alembic migration for 6 tables
- [ ] Implement API endpoints
- [ ] Write scoring algorithms
- [ ] Begin frontend component development

### Week 8 (Phase 2.0 End):
- [ ] Launch beta test with 20-30 students
- [ ] Collect feedback
- [ ] Plan Phase 2.5 (Combined Insights)

---

**Status:** 📋 **PLANNING COMPLETE**  
**Ready for Implementation:** Phase 2.0 (Mar 2026)  
**Expected Impact:** Transform DreamSeed AI from academic testing tool to comprehensive career guidance platform  

---

**End of Phase 2 Master Plan**
