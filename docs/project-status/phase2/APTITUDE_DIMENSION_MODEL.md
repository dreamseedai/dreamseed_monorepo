# DreamSeed AI - Aptitude Dimension Model (4-Track Framework)

**Version:** 2.0  
**Date:** November 24, 2025  
**Status:** 📋 Design Complete  

---

## 🎯 Overview

DreamSeed AI의 적성검사는 **학업 능력(CAT θ) + 적성·흥미 프로파일**을 결합하여  
학생에게 최적의 **전공/트랙 추천**을 제공하는 것을 목표로 합니다.

### Core Philosophy

```
Academic Ability (CAT/IRT)  →  "What you CAN do"
        +
Aptitude Profile (Interest)  →  "What you WANT to do"
        ↓
Personalized Major/Career Recommendation
```

---

## 🧱 4-Track Dimension Framework

### Primary Dimensions (Phase 2.0)

각 차원은 **-1.0 ~ +1.0** 범위의 연속형 점수로 표현됩니다.

| Dimension | Symbol | Description | Example Majors | Key Traits |
|-----------|--------|-------------|----------------|------------|
| **STEM Aptitude** | S | 논리·수리적 사고, 패턴 인식, 시스템적 문제 해결 | Engineering, CS, Physics, Math, Pre-Med | 논리 문제 선호, 수학적 추론, 과학 실험 흥미 |
| **Humanities / Verbal** | H | 언어 능력, 글쓰기, 발표, 역사/철학·심리 탐구 | Literature, Law, Sociology, Communication, International Studies | 글쓰기 선호, 토론 능력, 사회 문제 관심 |
| **Creative / Artistic** | A | 미적 감각, 창작, 디자인, 상상력, 표현 선호 | Design, Architecture, Film/Music, Fine Arts | 창작 활동 선호, 자유로운 사고, 디자인 감각 |
| **Practical / Hands-on** | P | 도구 사용, 실습 선호, 현실적·구체적 문제 해결 | Nursing, Culinary, Mechanical/Electrical, Vocational | 실습 선호, 손재주, 현실적 문제 해결 |

---

### Secondary Dimensions (Phase 2.5 - Future)

| Dimension | Symbol | Description | Use Case |
|-----------|--------|-------------|----------|
| **Social/People Orientation** | SOC | 타인과의 상호작용, 협업, 교육·상담 선호 | Education, Social Work, HR, Counseling |
| **Leadership/Initiative** | LEAD | 리더십, 주도성, 조직 관리 능력 | Management, Entrepreneurship, Politics |

---

## 📋 Dimension Measurement Strategy

### Question Distribution (40-item Survey)

| Dimension | Questions | Positive Items | Reverse-Scored |
|-----------|-----------|----------------|----------------|
| STEM (S) | 10 (Q1-Q10) | 8 | 2 |
| Humanities (H) | 10 (Q11-Q20) | 8 | 2 |
| Artistic (A) | 10 (Q21-Q30) | 8 | 2 |
| Practical (P) | 10 (Q31-Q40) | 8 | 2 |

**Total:** 40 items (expandable to 80 for Phase 2.5)

---

### Likert Scale (5-point)

| Response | Label | Raw Score | Converted Score |
|----------|-------|-----------|-----------------|
| 1 | 전혀 그렇지 않다 | 1 | -2 |
| 2 | 그렇지 않다 | 2 | -1 |
| 3 | 보통이다 | 3 | 0 |
| 4 | 그렇다 | 4 | +1 |
| 5 | 매우 그렇다 | 5 | +2 |

**Reverse-scored items:** Inverted before conversion  
(e.g., Response 1 → Score +2, Response 5 → Score -2)

---

## 🧮 Scoring Algorithm

### Step 1: Raw Score Conversion

For each question:
```python
def convert_likert_to_score(response: int, reverse_scored: bool = False) -> int:
    """
    Convert 1-5 Likert response to -2 to +2 scale.
    
    Args:
        response: 1-5 (Likert scale)
        reverse_scored: True if question is reverse-scored
    
    Returns:
        Score in range [-2, +2]
    """
    if reverse_scored:
        response = 6 - response  # Invert: 1→5, 2→4, 3→3, 4→2, 5→1
    
    return response - 3  # Convert to -2, -1, 0, +1, +2
```

---

### Step 2: Dimension Score Calculation

For each dimension (S, H, A, P):
```python
def calculate_dimension_score(responses: List[int], reverse_flags: List[bool]) -> float:
    """
    Calculate dimension score from question responses.
    
    Args:
        responses: List of 10 responses (1-5)
        reverse_flags: List of 10 booleans indicating reverse scoring
    
    Returns:
        Dimension score in range [-1.0, +1.0]
    """
    converted_scores = [
        convert_likert_to_score(resp, rev)
        for resp, rev in zip(responses, reverse_flags)
    ]
    
    # Mean of converted scores
    mean_score = sum(converted_scores) / len(converted_scores)
    
    # Normalize to [-1.0, +1.0]
    normalized = mean_score / 2.0
    
    return round(normalized, 2)
```

**Example:**
- Student answers STEM questions: [5, 4, 5, 4, 3, 5, 4, 2, 5, 4]
- Reverse-scored flags: [False, False, True, False, False, False, False, True, False, False]
- Converted scores: [2, 1, -2, 1, 0, 2, 1, 1, 2, 1]
- Mean: 9 / 10 = 0.9
- Normalized: 0.9 / 2 = **0.45** (STEM score)

---

### Step 3: Profile Generation

```python
@dataclass
class AptitudeProfile:
    student_id: int
    stem_score: float          # -1.0 to +1.0
    humanities_score: float
    artistic_score: float
    practical_score: float
    survey_version: str
    completed_at: datetime
    
    def get_dominant_dimension(self) -> str:
        """Return dimension with highest score."""
        scores = {
            "STEM": self.stem_score,
            "Humanities": self.humanities_score,
            "Artistic": self.artistic_score,
            "Practical": self.practical_score
        }
        return max(scores, key=scores.get)
    
    def get_score_percentile(self, dimension: str, population_data: pd.DataFrame) -> int:
        """Calculate percentile rank compared to population."""
        score = getattr(self, f"{dimension.lower()}_score")
        return percentileofscore(population_data[dimension], score)
```

---

## 🎯 Track Mapping Strategy

### Track Definition

| Track | Primary Dimension | Secondary Dimension | Academic Threshold |
|-------|-------------------|---------------------|-------------------|
| **STEM Track** | S > 0.3 | Logical reasoning (from CAT) | Math θ > 0 |
| **Humanities Track** | H > 0.3 | Verbal ability (from CAT) | English θ > 0 |
| **Arts Track** | A > 0.5 | Creative expression | No strict threshold |
| **Practical Track** | P > 0.4 | Hands-on skills | Basic competency |

---

### Major Recommendation Rules

```python
def recommend_majors(profile: AptitudeProfile, academic_scores: dict) -> List[dict]:
    """
    Generate major recommendations based on aptitude + academic scores.
    
    Args:
        profile: AptitudeProfile object
        academic_scores: {"math_theta": 0.5, "english_theta": -0.2, ...}
    
    Returns:
        List of recommended majors with fit scores
    """
    recommendations = []
    
    # STEM majors
    if profile.stem_score > 0.3:
        stem_fit = calculate_stem_fit(profile, academic_scores)
        recommendations.extend([
            {"major": "Computer Science", "fit": stem_fit * 0.95, "track": "STEM"},
            {"major": "Engineering", "fit": stem_fit * 0.90, "track": "STEM"},
            {"major": "Physics/Math", "fit": stem_fit * 0.85, "track": "STEM"}
        ])
    
    # Humanities majors
    if profile.humanities_score > 0.3:
        hum_fit = calculate_humanities_fit(profile, academic_scores)
        recommendations.extend([
            {"major": "Law", "fit": hum_fit * 0.92, "track": "Humanities"},
            {"major": "Political Science", "fit": hum_fit * 0.88, "track": "Humanities"},
            {"major": "Literature", "fit": hum_fit * 0.85, "track": "Humanities"}
        ])
    
    # Arts majors
    if profile.artistic_score > 0.5:
        art_fit = calculate_artistic_fit(profile, academic_scores)
        recommendations.extend([
            {"major": "Design", "fit": art_fit * 0.90, "track": "Arts"},
            {"major": "Architecture", "fit": art_fit * 0.85, "track": "Arts"},
            {"major": "Film/Media", "fit": art_fit * 0.82, "track": "Arts"}
        ])
    
    # Practical majors
    if profile.practical_score > 0.4:
        prac_fit = calculate_practical_fit(profile, academic_scores)
        recommendations.extend([
            {"major": "Nursing", "fit": prac_fit * 0.88, "track": "Practical"},
            {"major": "Engineering Tech", "fit": prac_fit * 0.85, "track": "Practical"},
            {"major": "Culinary Arts", "fit": prac_fit * 0.80, "track": "Practical"}
        ])
    
    # Sort by fit score and return top 5
    return sorted(recommendations, key=lambda x: x["fit"], reverse=True)[:5]
```

---

## 📊 Visualization Strategy

### Radar Chart (Spider Plot)

```
        STEM (0.74)
           /\
          /  \
         /    \
        /      \
       /________\
   Practical    Humanities
    (0.51)       (0.32)
       \        /
        \      /
         \    /
          \  /
           \/
        Artistic
         (0.13)
```

**Frontend Library:** Chart.js, Recharts, or D3.js

---

### Bar Chart (Percentile Comparison)

```
STEM:       ████████████████░░░░  80th %ile
Humanities: ████████░░░░░░░░░░░░  40th %ile
Artistic:   ███░░░░░░░░░░░░░░░░░  15th %ile
Practical:  ████████████░░░░░░░░  60th %ile
```

---

### Profile Summary Card

```
┌─────────────────────────────────────────┐
│  🎯 Your Dominant Dimension: STEM       │
├─────────────────────────────────────────┤
│  Top Strength:                          │
│  • Logical problem solving              │
│  • Mathematical reasoning               │
│  • Systems thinking                     │
│                                         │
│  Recommended Tracks:                    │
│  1. Computer Science (95% fit)          │
│  2. Engineering (90% fit)               │
│  3. Data Science (88% fit)              │
└─────────────────────────────────────────┘
```

---

## 🔬 Psychometric Properties (Target)

### Reliability (Cronbach's Alpha)

| Dimension | Target α | Status |
|-----------|----------|--------|
| STEM | > 0.80 | To be validated |
| Humanities | > 0.80 | To be validated |
| Artistic | > 0.75 | To be validated |
| Practical | > 0.75 | To be validated |

**Validation Plan:** Beta test with 100+ students, compute internal consistency.

---

### Validity

**Construct Validity:**
- Correlation with academic performance (θ scores)
- Correlation with self-reported major interest
- Discriminant validity between dimensions (r < 0.5)

**Predictive Validity:**
- Track actual major choice after 1 year
- Measure satisfaction with recommended majors

---

## 🚀 Implementation Roadmap

### Phase 2.0 (8 weeks)

**Week 1-2: Item Development**
- [ ] Write 80 candidate questions (20 per dimension)
- [ ] Expert review (educators, psychometricians)
- [ ] Pilot test with 30 students
- [ ] Select best 40 items (10 per dimension)

**Week 3-4: Backend Implementation**
- [ ] Database schema (aptitude_questions, responses, profiles)
- [ ] Scoring algorithm implementation
- [ ] API endpoints (start, submit, results)
- [ ] Unit tests (100% coverage)

**Week 5-6: Frontend Development**
- [ ] Question UI (Likert scale component)
- [ ] Progress indicator
- [ ] Results page (radar chart, percentile bars)
- [ ] Profile dashboard integration

**Week 7: Integration Testing**
- [ ] E2E test scenarios
- [ ] Performance testing (1000+ responses)
- [ ] Beta deployment

**Week 8: Validation Study**
- [ ] 100-student beta test
- [ ] Reliability analysis (Cronbach's α)
- [ ] Validity correlations
- [ ] Production release

---

### Phase 2.5 (Future)

- [ ] Secondary dimensions (Social, Leadership)
- [ ] 80-item extended survey
- [ ] Machine learning-based recommendations
- [ ] LLM-powered personalized feedback
- [ ] Parent/Teacher dashboard

---

## 📄 Related Documents

- [APTITUDE_SAMPLE_QUESTIONS.md](./APTITUDE_SAMPLE_QUESTIONS.md) - 40 sample items with scoring
- [PHASE2_APTITUDE_ASSESSMENT.md](./PHASE2_APTITUDE_ASSESSMENT.md) - Complete technical spec
- [PHASE2_MASTER_PLAN.md](./PHASE2_MASTER_PLAN.md) - Overall Phase 2 roadmap
- [COMBINED_RECOMMENDATION_MODEL.md](./COMBINED_RECOMMENDATION_MODEL.md) - Academic + Aptitude integration

---

**Status:** 📋 **DESIGN COMPLETE**  
**Next Step:** Week 1 - Item Development & Expert Review  

---

**End of Aptitude Dimension Model**
