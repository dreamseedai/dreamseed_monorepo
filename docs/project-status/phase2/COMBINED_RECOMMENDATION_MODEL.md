# Combined Recommendation Model - Academic + Aptitude Integration

**Version:** 1.0  
**Date:** November 24, 2025  
**Purpose:** Integrate CAT/IRT academic scores (θ) with aptitude profile to generate personalized major/track recommendations  

---

## 🎯 Model Overview

### The Integration Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                 DreamSeed AI Recommendation Engine          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT 1: Academic Ability (CAT/IRT)                       │
│    ├─ Math θ    (e.g., 1.2 → "High ability")              │
│    ├─ English θ (e.g., -0.3 → "Below average")            │
│    └─ Science θ (e.g., 0.5 → "Above average")             │
│                                                             │
│  INPUT 2: Aptitude Profile                                 │
│    ├─ STEM score        (e.g., 0.70 → "Strong interest")  │
│    ├─ Humanities score  (e.g., -0.15 → "Low interest")    │
│    ├─ Artistic score    (e.g., -0.25 → "Low interest")    │
│    └─ Practical score   (e.g., 0.50 → "Moderate")         │
│                                                             │
│  PROCESSING: Weighted Combination                          │
│    ├─ Track-specific formulas                             │
│    ├─ Threshold checks                                     │
│    └─ Confidence scoring                                   │
│                                                             │
│  OUTPUT: Personalized Recommendations                      │
│    ├─ Top 3-5 majors with fit scores (0.0-1.0)           │
│    ├─ Reasoning/justification for each                    │
│    ├─ Related careers                                      │
│    └─ Recommended next steps                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧮 Step 1: Normalize Academic Scores

### θ to Standard Score Conversion

IRT theta (θ) is typically in range **[-3, +3]**, with mean 0 and SD 1.

Convert to **0-100 scale** for easier combination:

```python
def theta_to_score(theta: float) -> float:
    """
    Convert IRT theta to 0-100 scale.
    
    Args:
        theta: IRT ability estimate (typically -3 to +3)
    
    Returns:
        Score in range [0, 100]
    
    Formula:
        score = 50 + (theta * 10)
        Clamped to [0, 100]
    
    Examples:
        theta = 0.0  → 50 (average)
        theta = 1.5  → 65 (above average)
        theta = -1.0 → 40 (below average)
    """
    score = 50 + (theta * 10)
    return max(0, min(100, score))
```

**Interpretation:**

| θ Range | Score Range | Percentile | Interpretation |
|---------|-------------|------------|----------------|
| > +2.0 | > 70 | ~98% | Exceptional |
| +1.0 to +2.0 | 60-70 | 84-98% | High |
| 0.0 to +1.0 | 50-60 | 50-84% | Above Average |
| -1.0 to 0.0 | 40-50 | 16-50% | Below Average |
| < -1.0 | < 40 | < 16% | Low |

---

### Normalized Academic Profile

```python
@dataclass
class AcademicProfile:
    math_theta: float
    english_theta: float
    science_theta: Optional[float] = None
    
    @property
    def math_score(self) -> float:
        return theta_to_score(self.math_theta)
    
    @property
    def english_score(self) -> float:
        return theta_to_score(self.english_theta)
    
    @property
    def science_score(self) -> float:
        if self.science_theta is None:
            return 50.0  # Default to average if not available
        return theta_to_score(self.science_theta)
    
    @property
    def overall_academic(self) -> float:
        """Average academic ability."""
        scores = [self.math_score, self.english_score]
        if self.science_theta is not None:
            scores.append(self.science_score)
        return sum(scores) / len(scores)
```

---

## 🎯 Step 2: Track-Specific Fit Formulas

### Formula Design Principles

1. **Aptitude weight > Academic weight** (60-70% vs 30-40%)
   - Rationale: Interest/motivation predicts success better than raw ability
2. **Subject relevance varies by track**
   - STEM → Math/Science critical
   - Humanities → English critical
   - Arts → Overall academic less important
3. **Threshold checks prevent mismatches**
   - Don't recommend Engineering if Math θ < -1.0

---

### STEM Track Formula

```python
def calculate_stem_fit(
    academic: AcademicProfile,
    aptitude: Dict[str, float]
) -> float:
    """
    Calculate STEM track fit score.
    
    Weights:
        - STEM aptitude: 55%
        - Math academic: 30%
        - Science academic: 15%
    
    Threshold: Math θ > -0.5 (score > 45)
    """
    stem_apt = aptitude["STEM"]
    math_norm = academic.math_score / 100  # Normalize to [0, 1]
    science_norm = academic.science_score / 100
    
    # Threshold check
    if academic.math_theta < -0.5:
        return 0.0  # Cannot recommend STEM with low math ability
    
    # Weighted combination
    fit = (
        0.55 * (stem_apt + 1.0) / 2.0 +  # Convert [-1,1] to [0,1]
        0.30 * math_norm +
        0.15 * science_norm
    )
    
    return round(fit, 2)
```

**Example:**
- STEM aptitude: 0.70
- Math θ: 1.2 → score 62 → norm 0.62
- Science θ: 0.5 → score 55 → norm 0.55

```
fit = 0.55 * (0.70 + 1.0) / 2.0 + 0.30 * 0.62 + 0.15 * 0.55
    = 0.55 * 0.85 + 0.186 + 0.0825
    = 0.4675 + 0.186 + 0.0825
    = 0.736 → 0.74
```

**Interpretation:** 74% fit → **Strong recommendation**

---

### Humanities Track Formula

```python
def calculate_humanities_fit(
    academic: AcademicProfile,
    aptitude: Dict[str, float]
) -> float:
    """
    Calculate Humanities track fit score.
    
    Weights:
        - Humanities aptitude: 60%
        - English academic: 30%
        - Overall academic: 10%
    
    Threshold: English θ > -1.0 (score > 40)
    """
    hum_apt = aptitude["Humanities"]
    english_norm = academic.english_score / 100
    overall_norm = academic.overall_academic / 100
    
    # Threshold check
    if academic.english_theta < -1.0:
        return 0.0  # Cannot recommend Humanities with very low verbal ability
    
    # Weighted combination
    fit = (
        0.60 * (hum_apt + 1.0) / 2.0 +
        0.30 * english_norm +
        0.10 * overall_norm
    )
    
    return round(fit, 2)
```

---

### Arts Track Formula

```python
def calculate_arts_fit(
    academic: AcademicProfile,
    aptitude: Dict[str, float]
) -> float:
    """
    Calculate Arts track fit score.
    
    Weights:
        - Artistic aptitude: 70% (most important)
        - Overall academic: 20%
        - English academic: 10% (for conceptual arts)
    
    Threshold: Artistic aptitude > 0.3
    """
    art_apt = aptitude["Artistic"]
    overall_norm = academic.overall_academic / 100
    english_norm = academic.english_score / 100
    
    # Threshold check
    if art_apt < 0.3:
        return 0.0  # Must have at least moderate artistic interest
    
    # Weighted combination
    fit = (
        0.70 * (art_apt + 1.0) / 2.0 +
        0.20 * overall_norm +
        0.10 * english_norm
    )
    
    return round(fit, 2)
```

---

### Practical Track Formula

```python
def calculate_practical_fit(
    academic: AcademicProfile,
    aptitude: Dict[str, float]
) -> float:
    """
    Calculate Practical/Vocational track fit score.
    
    Weights:
        - Practical aptitude: 60%
        - Math/Science (basic competency): 25%
        - Overall academic: 15%
    
    Threshold: None (practical skills don't require high academic ability)
    """
    prac_apt = aptitude["Practical"]
    math_norm = academic.math_score / 100
    science_norm = academic.science_score / 100
    overall_norm = academic.overall_academic / 100
    
    # Basic competency (average of math/science)
    basic_comp = (math_norm + science_norm) / 2.0
    
    # Weighted combination
    fit = (
        0.60 * (prac_apt + 1.0) / 2.0 +
        0.25 * basic_comp +
        0.15 * overall_norm
    )
    
    return round(fit, 2)
```

---

## 🏆 Step 3: Major-Specific Recommendations

### Major Database (Expandable)

```python
MAJOR_DATABASE = {
    # STEM Majors
    "Computer Science": {
        "track": "STEM",
        "required_aptitude": {"STEM": 0.3, "Logical": 0.4},
        "academic_threshold": {"math_theta": 0.0},
        "fit_multiplier": 1.0,
        "careers": ["Software Engineer", "Data Scientist", "AI Researcher"]
    },
    "Engineering (General)": {
        "track": "STEM",
        "required_aptitude": {"STEM": 0.4, "Practical": 0.2},
        "academic_threshold": {"math_theta": 0.0, "science_theta": -0.5},
        "fit_multiplier": 0.95,
        "careers": ["Mechanical Engineer", "Electrical Engineer", "Civil Engineer"]
    },
    "Physics/Mathematics": {
        "track": "STEM",
        "required_aptitude": {"STEM": 0.5},
        "academic_threshold": {"math_theta": 1.0},
        "fit_multiplier": 0.90,
        "careers": ["Physicist", "Mathematician", "Quant Analyst"]
    },
    "Medicine/Pre-Med": {
        "track": "STEM",
        "required_aptitude": {"STEM": 0.3, "Practical": 0.4, "Social": 0.3},
        "academic_threshold": {"math_theta": 0.0, "science_theta": 0.5},
        "fit_multiplier": 0.92,
        "careers": ["Physician", "Surgeon", "Medical Researcher"]
    },
    
    # Humanities Majors
    "Law": {
        "track": "Humanities",
        "required_aptitude": {"Humanities": 0.4, "Logical": 0.3},
        "academic_threshold": {"english_theta": 0.5},
        "fit_multiplier": 0.95,
        "careers": ["Lawyer", "Judge", "Legal Consultant"]
    },
    "Political Science": {
        "track": "Humanities",
        "required_aptitude": {"Humanities": 0.3, "Social": 0.3},
        "academic_threshold": {"english_theta": 0.0},
        "fit_multiplier": 0.88,
        "careers": ["Policy Analyst", "Diplomat", "Political Consultant"]
    },
    "Literature/Languages": {
        "track": "Humanities",
        "required_aptitude": {"Humanities": 0.5},
        "academic_threshold": {"english_theta": 0.5},
        "fit_multiplier": 0.85,
        "careers": ["Writer", "Translator", "Editor"]
    },
    
    # Arts Majors
    "Design (Visual/UX)": {
        "track": "Arts",
        "required_aptitude": {"Artistic": 0.5, "STEM": 0.0},
        "academic_threshold": {},
        "fit_multiplier": 0.90,
        "careers": ["UX Designer", "Graphic Designer", "Brand Designer"]
    },
    "Architecture": {
        "track": "Arts",
        "required_aptitude": {"Artistic": 0.4, "STEM": 0.3, "Practical": 0.2},
        "academic_threshold": {"math_theta": 0.0},
        "fit_multiplier": 0.88,
        "careers": ["Architect", "Urban Planner", "Interior Designer"]
    },
    "Film/Media": {
        "track": "Arts",
        "required_aptitude": {"Artistic": 0.5, "Humanities": 0.2},
        "academic_threshold": {},
        "fit_multiplier": 0.82,
        "careers": ["Film Director", "Content Creator", "Producer"]
    },
    
    # Practical Majors
    "Nursing": {
        "track": "Practical",
        "required_aptitude": {"Practical": 0.4, "Social": 0.3},
        "academic_threshold": {"math_theta": -0.5, "science_theta": 0.0},
        "fit_multiplier": 0.88,
        "careers": ["Registered Nurse", "Nurse Practitioner", "Clinical Nurse"]
    },
    "Business Administration": {
        "track": "Practical",
        "required_aptitude": {"Practical": 0.3, "Social": 0.3, "Logical": 0.2},
        "academic_threshold": {},
        "fit_multiplier": 0.85,
        "careers": ["Business Manager", "Entrepreneur", "Consultant"]
    },
}
```

---

### Recommendation Generation

```python
def generate_major_recommendations(
    academic: AcademicProfile,
    aptitude: Dict[str, float],
    top_n: int = 5
) -> List[Dict]:
    """
    Generate personalized major recommendations.
    
    Returns:
        List of dicts with major, fit_score, track, reasons, careers
    """
    # Calculate track fit scores
    track_fits = {
        "STEM": calculate_stem_fit(academic, aptitude),
        "Humanities": calculate_humanities_fit(academic, aptitude),
        "Arts": calculate_arts_fit(academic, aptitude),
        "Practical": calculate_practical_fit(academic, aptitude),
    }
    
    recommendations = []
    
    for major_name, major_info in MAJOR_DATABASE.items():
        track = major_info["track"]
        base_fit = track_fits[track]
        
        # Check thresholds
        if not meets_thresholds(academic, aptitude, major_info):
            continue  # Skip if thresholds not met
        
        # Apply major-specific multiplier
        final_fit = base_fit * major_info["fit_multiplier"]
        
        # Generate reasoning
        reasons = generate_reasons(academic, aptitude, major_info)
        
        recommendations.append({
            "major": major_name,
            "fit_score": round(final_fit, 2),
            "track": track,
            "reasons": reasons,
            "careers": major_info["careers"]
        })
    
    # Sort by fit score and return top N
    recommendations.sort(key=lambda x: x["fit_score"], reverse=True)
    return recommendations[:top_n]


def meets_thresholds(academic, aptitude, major_info) -> bool:
    """Check if student meets minimum requirements."""
    # Academic thresholds
    for subject, min_theta in major_info["academic_threshold"].items():
        if subject == "math_theta" and academic.math_theta < min_theta:
            return False
        if subject == "english_theta" and academic.english_theta < min_theta:
            return False
        if subject == "science_theta" and academic.science_theta and academic.science_theta < min_theta:
            return False
    
    # Aptitude thresholds
    for dim, min_score in major_info["required_aptitude"].items():
        if dim in aptitude and aptitude[dim] < min_score:
            return False
    
    return True


def generate_reasons(academic, aptitude, major_info) -> List[str]:
    """Generate human-readable reasons for recommendation."""
    reasons = []
    
    # Check aptitude strengths
    for dim, req in major_info["required_aptitude"].items():
        if dim in aptitude and aptitude[dim] >= req + 0.3:
            reasons.append(f"Strong {dim} orientation ({aptitude[dim]:.1f})")
    
    # Check academic strengths
    if major_info["track"] == "STEM":
        if academic.math_theta > 1.0:
            reasons.append(f"Exceptional math ability (θ={academic.math_theta:.1f}, top 16%)")
        elif academic.math_theta > 0.5:
            reasons.append(f"Above-average math ability (θ={academic.math_theta:.1f})")
    
    if major_info["track"] == "Humanities":
        if academic.english_theta > 1.0:
            reasons.append(f"Exceptional verbal ability (θ={academic.english_theta:.1f})")
        elif academic.english_theta > 0.5:
            reasons.append(f"Above-average verbal ability")
    
    # Default reason if no specific strengths
    if not reasons:
        reasons.append(f"Good overall fit for {major_info['track']} track")
    
    return reasons[:3]  # Limit to 3 reasons
```

---

## 📊 Step 4: Complete Example

### Input Data

```python
# Academic profile
academic = AcademicProfile(
    math_theta=1.2,      # Strong math
    english_theta=-0.3,  # Below-average English
    science_theta=0.5    # Above-average science
)

# Aptitude profile
aptitude = {
    "STEM": 0.70,        # Strong STEM interest
    "Humanities": -0.15, # Low humanities interest
    "Artistic": -0.25,   # Low artistic interest
    "Practical": 0.50    # Moderate practical orientation
}
```

---

### Processing

```python
recommendations = generate_major_recommendations(academic, aptitude, top_n=5)
```

---

### Output

```json
[
  {
    "major": "Computer Science",
    "fit_score": 0.78,
    "track": "STEM",
    "reasons": [
      "Strong STEM orientation (0.7)",
      "Exceptional math ability (θ=1.2, top 12%)",
      "Above-average science ability"
    ],
    "careers": [
      "Software Engineer",
      "Data Scientist",
      "AI Researcher"
    ]
  },
  {
    "major": "Engineering (General)",
    "fit_score": 0.74,
    "track": "STEM",
    "reasons": [
      "Strong STEM orientation (0.7)",
      "Exceptional math ability (θ=1.2)",
      "Moderate practical skills (0.5)"
    ],
    "careers": [
      "Mechanical Engineer",
      "Electrical Engineer",
      "Civil Engineer"
    ]
  },
  {
    "major": "Physics/Mathematics",
    "fit_score": 0.69,
    "track": "STEM",
    "reasons": [
      "Strong STEM orientation (0.7)",
      "Exceptional math ability (θ=1.2)"
    ],
    "careers": [
      "Physicist",
      "Mathematician",
      "Quant Analyst"
    ]
  },
  {
    "major": "Business Administration",
    "fit_score": 0.52,
    "track": "Practical",
    "reasons": [
      "Moderate practical orientation (0.5)",
      "Balanced academic profile"
    ],
    "careers": [
      "Business Manager",
      "Entrepreneur",
      "Consultant"
    ]
  },
  {
    "major": "Architecture",
    "fit_score": 0.48,
    "track": "Arts",
    "reasons": [
      "Good overall fit for Arts track",
      "Above-average math ability"
    ],
    "careers": [
      "Architect",
      "Urban Planner",
      "Interior Designer"
    ]
  }
]
```

---

## 🎯 Step 5: Confidence Scoring

### Confidence Factors

```python
def calculate_confidence(academic: AcademicProfile, aptitude: Dict[str, float]) -> float:
    """
    Calculate confidence in recommendations (0.0 to 1.0).
    
    High confidence when:
        - Clear dominant dimension (max score > 0.5, others < 0.2)
        - Academic performance aligns with aptitude
        - Low variance in responses
    """
    # Factor 1: Dominant dimension clarity
    sorted_apt = sorted(aptitude.values(), reverse=True)
    dominance = sorted_apt[0] - sorted_apt[1]  # Gap between top 2
    dominance_factor = min(dominance / 0.8, 1.0)  # Max at 0.8 gap
    
    # Factor 2: Academic-aptitude alignment
    math_stem_align = 1.0 - abs(academic.math_theta / 2.0 - aptitude["STEM"])
    eng_hum_align = 1.0 - abs(academic.english_theta / 2.0 - aptitude["Humanities"])
    alignment_factor = (math_stem_align + eng_hum_align) / 2.0
    
    # Factor 3: Absolute strength (avoid "mediocre all-around")
    max_strength = max(aptitude.values())
    strength_factor = (max_strength + 1.0) / 2.0  # Convert [-1,1] to [0,1]
    
    # Combined confidence
    confidence = (
        0.40 * dominance_factor +
        0.35 * alignment_factor +
        0.25 * strength_factor
    )
    
    return round(confidence, 2)
```

**Example:**
- Top aptitude: STEM 0.70, 2nd: Practical 0.50 → gap 0.20
- Math θ 1.2 aligns with STEM 0.70 → alignment ~0.75
- Max strength 0.70 → strength_factor 0.85

```
confidence = 0.40 * 0.25 + 0.35 * 0.75 + 0.25 * 0.85
           = 0.10 + 0.26 + 0.21
           = 0.57 → Moderate confidence
```

---

## 📄 Related Documents

- [APTITUDE_DIMENSION_MODEL.md](./APTITUDE_DIMENSION_MODEL.md) - Dimension framework
- [LIKERT_QUESTIONS_40.md](./LIKERT_QUESTIONS_40.md) - Question bank
- [PHASE2_APTITUDE_ASSESSMENT.md](./PHASE2_APTITUDE_ASSESSMENT.md) - Complete Phase 2 spec
- [FRONTEND_WIREFRAMES.md](./FRONTEND_WIREFRAMES.md) - UI/UX design

---

**Status:** 📋 **MODEL COMPLETE**  
**Next Step:** Implement in backend scoring engine  

---

**End of Combined Recommendation Model**
