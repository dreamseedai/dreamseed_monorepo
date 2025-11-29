# 학습 분석 및 리포팅 엔진 (Analytics & Reporting Engine)

학습 분석 및 리포팅 엔진은 학생의 시험 결과와 학습 활동 데이터를 분석하여 유의미한 인사이트와 리포트를 생성하는 핵심 서비스입니다. 이 엔진은 DreamSeedAI가 개인 맞춤 학습 경험을 제공하고, 데이터 기반 의사 결정을 지원하는 데 중요한 역할을 합니다.

## 목차

1. [목표](#목표)
2. [주요 기능](#주요-기능)
3. [데이터 수집](#데이터-수집)
4. [분석 방법론](#분석-방법론)
5. [AI 모델](#ai-모델)
6. [추천 시스템](#추천-시스템)
7. [피드백 생성](#피드백-생성)
8. [리포트 생성](#리포트-생성)
9. [구현 예시](#구현-예시)
10. [기술 스택](#기술-스택)
11. [거버넌스 통합](#거버넌스-통합)

---

## 목표

- **학습자 프로파일 생성**: 학생의 역량, 강점, 약점, 학습 스타일 등을 종합적으로 파악하여 프로필을 생성합니다.
- **성과 분석**: 시험 결과, 과제 수행, 튜터링 참여 등 다양한 데이터를 분석하여 학습 성과를 측정하고 평가합니다.
- **개인화된 피드백 제공**: 학생 개개인에게 맞는 맞춤형 피드백과 개선 방안을 제시합니다.
- **데이터 기반 의사 결정 지원**: 교사와 관리자가 학생의 학습을 효과적으로 지원할 수 있도록 필요한 정보를 제공합니다.
- **문항 품질 관리**: 문항의 난이도, 변별도, 및 학생들의 반응 데이터를 분석하여 문항 은행의 품질을 개선합니다.

---

## 주요 기능

### 1. 데이터 수집

학생의 모든 정답/오답, 소요 시간, 힌트 사용, 학습 자료 접근 등 학습 활동 데이터를 수집합니다.

**수집 데이터 유형**:
- 시험 응답 (정답/오답, 소요 시간)
- 과제 제출 (완료율, 점수)
- AI 튜터링 상호작용 (질문 수, 힌트 사용)
- 학습 자료 접근 (동영상 시청, 자료 다운로드)
- 학습 패턴 (접속 시간, 학습 빈도)

### 2. 통계 분석

수집된 데이터를 기반으로 기본적인 통계 분석 (평균, 표준편차, 빈도 등)을 수행합니다.

### 3. AI 모델

- **IRT (Item Response Theory) 모델**: 학생 능력치 및 문항 난이도 추정
- **시계열 분석**: 학생 능력 변화 추적 및 예측
- **혼합 효과 모델**: 성적에 영향을 미치는 요인 분석
- **추천 시스템**: 개인화된 학습 콘텐츠 추천

---

## 데이터 수집

### 학습 활동 데이터 스키마

```sql
-- 학습 기록 테이블
CREATE TABLE learning_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    activity_type VARCHAR(50) NOT NULL,  -- 'exam', 'assignment', 'tutoring', 'video'
    
    -- 시험/과제 관련
    item_id VARCHAR(50) REFERENCES items(item_id),
    score INTEGER,  -- 1 (정답) or 0 (오답)
    response TEXT,
    time_spent_seconds INTEGER,
    
    -- 튜터링 관련
    session_id UUID,
    hints_used INTEGER DEFAULT 0,
    questions_asked INTEGER DEFAULT 0,
    
    -- 학습 자료 관련
    resource_id UUID,
    completion_rate DECIMAL(5,2),  -- 0.00 ~ 100.00
    
    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- 학생 프로파일 테이블
CREATE TABLE student_profiles (
    student_id UUID PRIMARY KEY REFERENCES students(id),
    
    -- 능력치
    current_theta DECIMAL(5,3),
    theta_history JSONB,  -- [{"date": "2025-01-01", "theta": 0.5}, ...]
    
    -- 강점/약점
    strong_concepts TEXT[],
    weak_concepts TEXT[],
    
    -- 학습 스타일
    preferred_learning_time VARCHAR(20),  -- 'morning', 'afternoon', 'evening', 'night'
    average_session_duration INTEGER,  -- 분 단위
    study_frequency DECIMAL(3,1),  -- 주당 평균 학습 일수
    
    -- 통계
    total_study_time INTEGER,  -- 분 단위
    total_exams_taken INTEGER,
    average_score DECIMAL(5,2),
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_learning_records_student_created ON learning_records(student_id, created_at DESC);
CREATE INDEX idx_learning_records_activity_type ON learning_records(activity_type);
CREATE INDEX idx_learning_records_item_id ON learning_records(item_id);
```

### 데이터 수집 API

```python
from fastapi import FastAPI, Request
from datetime import datetime, timezone

app = FastAPI()

@app.post("/api/analytics/record-activity")
async def record_learning_activity(
    request: Request,
    student_id: str,
    activity_type: str,
    activity_data: dict
):
    """
    학습 활동 기록
    
    Args:
        student_id: 학생 ID
        activity_type: 활동 유형 ('exam', 'assignment', 'tutoring', 'video')
        activity_data: 활동 데이터
    """
    # 학습 기록 저장
    record_id = await db.execute(
        """
        INSERT INTO learning_records 
        (student_id, activity_type, item_id, score, response, time_spent_seconds,
         session_id, hints_used, resource_id, completion_rate, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """,
        student_id,
        activity_type,
        activity_data.get('item_id'),
        activity_data.get('score'),
        activity_data.get('response'),
        activity_data.get('time_spent_seconds'),
        activity_data.get('session_id'),
        activity_data.get('hints_used', 0),
        activity_data.get('resource_id'),
        activity_data.get('completion_rate'),
        json.dumps(activity_data.get('metadata', {}))
    )
    
    # 학생 프로파일 업데이트 (비동기)
    await update_student_profile_async(student_id)
    
    return {"record_id": record_id}
```

---

## 분석 방법론

### 1. IRT 모델 및 계층적 베이지안 모델

학생 능력의 변화를 시계열로 추정하고, 혼합 효과 모형으로 어떤 요인이 성과에 영향을 주는지 분석합니다.

**예시**: 학생의 최근 3번의 모의고사 데이터를 이용하여 향상도 곡선을 추정하고, 향후 목표 점수 도달 가능 시점을 예측합니다.

```python
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta

async def estimate_ability_trajectory(student_id: str, lookback_days: int = 90):
    """
    학생 능력치 시계열 추정
    
    Args:
        student_id: 학생 ID
        lookback_days: 분석 기간 (일)
    
    Returns:
        능력치 변화 데이터
    """
    # 최근 시험 결과 조회
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    exam_results = await db.fetch_all(
        """
        SELECT exam_date, final_theta, standard_error
        FROM exam_sessions
        WHERE student_id = $1 AND exam_date >= $2
        ORDER BY exam_date ASC
        """,
        student_id, cutoff_date
    )
    
    if len(exam_results) < 2:
        return None  # 데이터 부족
    
    # 시간-능력치 데이터 변환
    dates = [r['exam_date'] for r in exam_results]
    thetas = [r['final_theta'] for r in exam_results]
    
    # 선형 회귀로 추세 추정
    from sklearn.linear_model import LinearRegression
    
    # 날짜를 숫자로 변환 (첫 날을 0으로)
    X = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
    y = np.array(thetas)
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 향상률 (일일 theta 증가량)
    improvement_rate = model.coef_[0]
    
    # 향후 예측 (30일)
    future_days = np.arange(X[-1][0], X[-1][0] + 30).reshape(-1, 1)
    predicted_thetas = model.predict(future_days)
    
    return {
        "current_theta": thetas[-1],
        "improvement_rate": improvement_rate,  # theta/day
        "trend": "improving" if improvement_rate > 0 else "declining",
        "predicted_theta_30days": predicted_thetas[-1],
        "historical_data": [
            {"date": d.isoformat(), "theta": t}
            for d, t in zip(dates, thetas)
        ]
    }

async def predict_target_achievement(
    student_id: str,
    target_score: float,
    exam_type: str
):
    """
    목표 점수 도달 시점 예측
    
    Args:
        student_id: 학생 ID
        target_score: 목표 점수 (0-100)
        exam_type: 시험 유형
    
    Returns:
        예상 도달 일자
    """
    # 능력치 추세 분석
    trajectory = await estimate_ability_trajectory(student_id)
    
    if not trajectory or trajectory['improvement_rate'] <= 0:
        return {"achievable": False, "reason": "향상 추세가 없습니다"}
    
    # 목표 점수를 theta로 변환
    from services.assessment_engine import convert_score_to_theta
    target_theta = convert_score_to_theta(target_score, exam_type)
    
    # 현재 theta
    current_theta = trajectory['current_theta']
    
    # 필요한 theta 증가량
    theta_gap = target_theta - current_theta
    
    if theta_gap <= 0:
        return {"achievable": True, "days": 0, "message": "이미 목표를 달성했습니다"}
    
    # 예상 소요 일수
    improvement_rate = trajectory['improvement_rate']
    estimated_days = theta_gap / improvement_rate
    
    # 예상 도달 일자
    achievement_date = datetime.now(timezone.utc) + timedelta(days=estimated_days)
    
    return {
        "achievable": True,
        "estimated_days": round(estimated_days),
        "achievement_date": achievement_date.isoformat(),
        "current_theta": current_theta,
        "target_theta": target_theta,
        "daily_improvement": improvement_rate
    }
```

### 2. 통계 재계산 (문항 품질 관리)

각 문항의 통계 (난이도, 변별도)를 지속적으로 재계산하여 문항 은행에 피드백 루프를 형성합니다.

많이 틀리는 문항이 실제로 너무 어렵거나 모호하면 그 문항의 난이도를 상향 조정하거나 플래그로 표시해 콘텐츠 팀이 검토하도록 합니다.

```python
async def recalculate_item_statistics(item_id: str):
    """
    문항 통계 재계산 (배치 작업)
    
    Args:
        item_id: 문항 ID
    """
    # 해당 문항에 대한 모든 응답 조회
    responses = await db.fetch_all(
        """
        SELECT student_id, score, time_spent_seconds
        FROM learning_records
        WHERE item_id = $1 AND activity_type = 'exam'
        """,
        item_id
    )
    
    if len(responses) < 30:
        return None  # 데이터 부족
    
    # 기본 통계
    total_count = len(responses)
    correct_count = sum(r['score'] for r in responses)
    accuracy = correct_count / total_count
    
    avg_time = np.mean([r['time_spent_seconds'] for r in responses])
    
    # IRT 파라미터 재계산 (content_management.py 참조)
    from services.content_management import calibrate_item_parameters
    new_params = await calibrate_item_parameters(item_id)
    
    # 이상 패턴 감지
    flags = []
    
    if accuracy > 0.95:
        flags.append("too_easy")
    elif accuracy < 0.05:
        flags.append("too_hard_or_ambiguous")
    
    if new_params and new_params['a'] < 0.3:
        flags.append("low_discrimination")
    
    # 통계 업데이트
    await db.execute(
        """
        UPDATE items
        SET total_count = $1,
            correct_count = $2,
            average_time_seconds = $3,
            quality_flags = $4,
            updated_at = NOW()
        WHERE item_id = $5
        """,
        total_count, correct_count, avg_time, flags, item_id
    )
    
    # 플래그가 있으면 콘텐츠 팀에 알림
    if flags:
        await notify_content_team(
            f"문항 {item_id}에 품질 이슈가 감지되었습니다: {', '.join(flags)}"
        )
    
    return {
        "item_id": item_id,
        "accuracy": accuracy,
        "avg_time": avg_time,
        "flags": flags,
        "new_params": new_params
    }
```

---

## AI 모델

### 1. 혼합 효과 모델 (Mixed Effects Model)

성적에 영향을 미치는 요인을 분석합니다.

```python
import statsmodels.formula.api as smf

async def analyze_performance_factors(student_id: str):
    """
    학생 성과에 영향을 미치는 요인 분석
    
    Returns:
        영향 요인 리스트
    """
    # 학습 기록 조회
    query = """
        SELECT 
            lr.score,
            lr.time_spent_seconds,
            lr.hints_used,
            lr.activity_type,
            DATE_PART('hour', lr.created_at) as hour_of_day,
            DATE_PART('dow', lr.created_at) as day_of_week,
            i.difficulty,
            i.discrimination
        FROM learning_records lr
        LEFT JOIN items i ON lr.item_id = i.item_id
        WHERE lr.student_id = $1 AND lr.activity_type IN ('exam', 'assignment')
    """
    
    data = await db.fetch_all(query, student_id)
    
    if len(data) < 50:
        return {"error": "데이터 부족 (최소 50개 필요)"}
    
    # DataFrame 변환
    import pandas as pd
    df = pd.DataFrame([dict(row) for row in data])
    
    # 혼합 효과 모델
    # score ~ difficulty + time_spent + hints_used + hour_of_day + (1|student)
    model = smf.mixedlm(
        "score ~ difficulty + time_spent_seconds + hints_used + C(hour_of_day)",
        data=df,
        groups=df["student_id"]
    )
    
    result = model.fit()
    
    # 유의미한 요인 추출
    significant_factors = []
    
    for param, pvalue in result.pvalues.items():
        if pvalue < 0.05 and param != "Intercept":
            coef = result.params[param]
            significant_factors.append({
                "factor": param,
                "coefficient": coef,
                "p_value": pvalue,
                "effect": "positive" if coef > 0 else "negative"
            })
    
    return {
        "significant_factors": significant_factors,
        "model_summary": result.summary().as_text()
    }
```

### 2. 시계열 분석 (ARIMA)

학생 능력 변화를 예측합니다.

```python
from statsmodels.tsa.arima.model import ARIMA

async def forecast_ability(student_id: str, periods: int = 30):
    """
    학생 능력치 예측 (ARIMA 모델)
    
    Args:
        student_id: 학생 ID
        periods: 예측 기간 (일)
    
    Returns:
        예측 결과
    """
    # theta 이력 조회
    profile = await db.fetch_one(
        "SELECT theta_history FROM student_profiles WHERE student_id = $1",
        student_id
    )
    
    theta_history = json.loads(profile['theta_history'])
    
    if len(theta_history) < 10:
        return {"error": "데이터 부족 (최소 10개 필요)"}
    
    # 시계열 데이터
    thetas = [h['theta'] for h in theta_history]
    
    # ARIMA 모델 (p=1, d=1, q=1)
    model = ARIMA(thetas, order=(1, 1, 1))
    fitted = model.fit()
    
    # 예측
    forecast = fitted.forecast(steps=periods)
    
    # 신뢰 구간
    forecast_ci = fitted.get_forecast(steps=periods).conf_int()
    
    return {
        "forecast": forecast.tolist(),
        "confidence_interval": {
            "lower": forecast_ci.iloc[:, 0].tolist(),
            "upper": forecast_ci.iloc[:, 1].tolist()
        }
    }
```

---

## 추천 시스템

학생들의 학습 콘텐츠 이용 기록, 시험 결과, 및 상호작용 패턴을 분석하여 개별 학생에게 최적화된 학습 콘텐츠 추천 (관련 자료, 강의 영상, 튜터링 세션 등).

### 협업 필터링 (Collaborative Filtering)

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

async def recommend_content_collaborative(
    student_id: str,
    content_type: str = "video",
    count: int = 5
) -> list[dict]:
    """
    협업 필터링 기반 콘텐츠 추천
    
    Args:
        student_id: 학생 ID
        content_type: 콘텐츠 유형 ('video', 'article', 'exercise')
        count: 추천 개수
    
    Returns:
        추천 콘텐츠 리스트
    """
    # 학생-콘텐츠 상호작용 매트릭스 구성
    query = """
        SELECT student_id, resource_id, 
               AVG(completion_rate) as avg_completion
        FROM learning_records
        WHERE activity_type = 'video' AND resource_id IS NOT NULL
        GROUP BY student_id, resource_id
    """
    
    interactions = await db.fetch_all(query)
    
    # DataFrame 변환
    import pandas as pd
    df = pd.DataFrame([dict(row) for row in interactions])
    
    # Pivot table (학생 x 콘텐츠)
    interaction_matrix = df.pivot_table(
        index='student_id',
        columns='resource_id',
        values='avg_completion',
        fill_value=0
    )
    
    # 학생 유사도 계산 (코사인 유사도)
    student_similarity = cosine_similarity(interaction_matrix)
    
    # 현재 학생의 인덱스
    try:
        student_idx = interaction_matrix.index.get_loc(student_id)
    except KeyError:
        return []  # 신규 학생
    
    # 유사한 학생 찾기 (상위 10명)
    similar_students_indices = student_similarity[student_idx].argsort()[-11:-1][::-1]
    similar_students = interaction_matrix.index[similar_students_indices]
    
    # 유사한 학생들이 본 콘텐츠 중 현재 학생이 안 본 것 추천
    current_student_contents = set(
        interaction_matrix.columns[interaction_matrix.loc[student_id] > 0]
    )
    
    recommendations = {}
    
    for similar_student in similar_students:
        similar_contents = interaction_matrix.columns[
            interaction_matrix.loc[similar_student] > 0
        ]
        
        for content_id in similar_contents:
            if content_id not in current_student_contents:
                score = interaction_matrix.loc[similar_student, content_id]
                recommendations[content_id] = recommendations.get(content_id, 0) + score
    
    # 상위 N개 추천
    top_recommendations = sorted(
        recommendations.items(),
        key=lambda x: x[1],
        reverse=True
    )[:count]
    
    # 콘텐츠 정보 조회
    content_ids = [r[0] for r in top_recommendations]
    contents = await db.fetch_all(
        "SELECT * FROM learning_resources WHERE id = ANY($1)",
        content_ids
    )
    
    return [dict(c) for c in contents]
```

### 콘텐츠 기반 필터링 (Content-Based)

```python
async def recommend_content_based(
    student_id: str,
    count: int = 5
) -> list[dict]:
    """
    콘텐츠 기반 추천 (취약 개념 기반)
    
    Args:
        student_id: 학생 ID
        count: 추천 개수
    
    Returns:
        추천 콘텐츠 리스트
    """
    # 취약 개념 파악
    from services.content_management import identify_weak_concepts
    weak_concepts = await identify_weak_concepts(student_id)
    
    if not weak_concepts:
        return []
    
    # 취약 개념 관련 콘텐츠 조회
    weak_concept_ids = [c['node_id'] for c in weak_concepts[:3]]  # 상위 3개
    
    query = """
        SELECT lr.*, kn.name as concept_name
        FROM learning_resources lr
        JOIN resource_knowledge_mapping rkm ON lr.id = rkm.resource_id
        JOIN knowledge_nodes kn ON rkm.node_id = kn.node_id
        WHERE rkm.node_id = ANY($1)
          AND lr.id NOT IN (
              SELECT resource_id FROM learning_records 
              WHERE student_id = $2 AND completion_rate > 80
          )
        ORDER BY lr.rating DESC, lr.view_count DESC
        LIMIT $3
    """
    
    contents = await db.fetch_all(query, weak_concept_ids, student_id, count)
    
    return [dict(c) for c in contents]
```

---

## 피드백 생성

학습 분석 엔진은 학생에게 제공할 피드백도 생성합니다.

### 템플릿 기반 피드백

```python
async def generate_personalized_feedback(student_id: str, exam_id: str) -> str:
    """
    개인화된 피드백 생성 (템플릿 기반)
    
    Args:
        student_id: 학생 ID
        exam_id: 시험 ID
    
    Returns:
        피드백 텍스트
    """
    # 시험 결과 조회
    exam_result = await db.fetch_one(
        """
        SELECT final_theta, final_score, items_answered
        FROM exam_sessions
        WHERE student_id = $1 AND id = $2
        """,
        student_id, exam_id
    )
    
    # 취약 개념 파악
    weak_concepts = await identify_weak_concepts_from_exam(student_id, exam_id)
    
    # 강점 개념 파악
    strong_concepts = await identify_strong_concepts_from_exam(student_id, exam_id)
    
    # 템플릿 기반 피드백 생성
    feedback_parts = []
    
    # 1. 전체 성적
    score = exam_result['final_score']
    if score >= 90:
        feedback_parts.append(f"🎉 우수한 성적입니다! ({score}점)")
    elif score >= 70:
        feedback_parts.append(f"✅ 양호한 성적입니다. ({score}점)")
    else:
        feedback_parts.append(f"📈 개선이 필요합니다. ({score}점)")
    
    # 2. 취약 개념
    if weak_concepts:
        top_weak = weak_concepts[0]
        accuracy = top_weak['accuracy'] * 100
        feedback_parts.append(
            f"\n⚠️ 취약 단원: {top_weak['name']}\n"
            f"   정답률: {accuracy:.0f}%\n"
            f"   권장 조치: {top_weak['name']} 단원의 개념 복습과 연습 문제 풀이가 필요합니다."
        )
    
    # 3. 강점 개념
    if strong_concepts:
        top_strong = strong_concepts[0]
        accuracy = top_strong['accuracy'] * 100
        feedback_parts.append(
            f"\n✨ 강점 단원: {top_strong['name']}\n"
            f"   정답률: {accuracy:.0f}%\n"
            f"   잘하고 있습니다! 이 수준을 유지하세요."
        )
    
    # 4. 학습 추천
    recommended_contents = await recommend_content_based(student_id, count=3)
    if recommended_contents:
        feedback_parts.append("\n📚 추천 학습 자료:")
        for content in recommended_contents:
            feedback_parts.append(f"   - {content['title']}")
    
    return "\n".join(feedback_parts)
```

### 생성형 AI 활용 (향후)

```python
import openai

async def generate_feedback_with_ai(student_id: str, exam_id: str) -> str:
    """
    생성형 AI 기반 피드백 생성
    
    Args:
        student_id: 학생 ID
        exam_id: 시험 ID
    
    Returns:
        AI 생성 피드백
    """
    # 학생 데이터 수집
    exam_result = await db.fetch_one(
        "SELECT * FROM exam_sessions WHERE student_id = $1 AND id = $2",
        student_id, exam_id
    )
    
    weak_concepts = await identify_weak_concepts_from_exam(student_id, exam_id)
    trajectory = await estimate_ability_trajectory(student_id)
    
    # AI 프롬프트
    prompt = f"""
    다음 학생의 시험 결과를 바탕으로 따뜻하고 격려적인 피드백을 작성하세요.
    
    시험 정보:
    - 점수: {exam_result['final_score']}점
    - 문항 수: {exam_result['items_answered']}개
    
    취약 개념:
    {chr(10).join([f"- {c['name']}: 정답률 {c['accuracy']*100:.0f}%" for c in weak_concepts[:3]])}
    
    학습 추세:
    - 최근 30일 향상률: {trajectory['improvement_rate']:.3f} theta/day
    - 추세: {trajectory['trend']}
    
    피드백 작성 가이드라인:
    1. 긍정적이고 격려적인 톤
    2. 구체적인 개선 방안 제시
    3. 학생의 노력 인정
    4. 3-5문장으로 간결하게
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    feedback = response.choices[0].message.content
    
    return feedback
```

---

## 리포트 생성

완료된 시험에 대한 리포트는 이 엔진이 Quarto/RMarkdown 등의 도구를 활용해 PDF/HTML로 자동 작성합니다.

### Quarto 기반 리포트 생성

```python
import subprocess
from pathlib import Path

async def generate_exam_report(
    student_id: str,
    exam_id: str,
    output_format: str = "pdf"
) -> str:
    """
    시험 리포트 생성 (Quarto)
    
    Args:
        student_id: 학생 ID
        exam_id: 시험 ID
        output_format: 출력 형식 ('pdf', 'html')
    
    Returns:
        리포트 파일 경로
    """
    # 데이터 수집
    exam_result = await get_exam_result(student_id, exam_id)
    student_profile = await get_student_profile(student_id)
    weak_concepts = await identify_weak_concepts_from_exam(student_id, exam_id)
    trajectory = await estimate_ability_trajectory(student_id)
    
    # Quarto 템플릿 렌더링
    template_path = "templates/exam_report.qmd"
    output_dir = f"/tmp/reports/{student_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 데이터 JSON 파일로 저장
    data_path = f"{output_dir}/data.json"
    with open(data_path, 'w') as f:
        json.dump({
            "exam_result": dict(exam_result),
            "student_profile": dict(student_profile),
            "weak_concepts": weak_concepts,
            "trajectory": trajectory
        }, f, ensure_ascii=False, indent=2)
    
    # Quarto 렌더링
    output_file = f"{output_dir}/report.{output_format}"
    
    subprocess.run([
        "quarto", "render", template_path,
        "--output", output_file,
        "--execute-params", data_path
    ], check=True)
    
    # S3 업로드
    s3_url = await upload_to_s3(output_file, f"reports/{student_id}/{exam_id}.{output_format}")
    
    return s3_url
```

### Quarto 템플릿 예시

```markdown
---
title: "시험 성적 리포트"
format: 
  pdf:
    documentclass: article
    geometry: margin=1in
execute:
  echo: false
params:
  data_path: "data.json"
---

```{python}
import json
import matplotlib.pyplot as plt
import pandas as pd

# 데이터 로드
with open(params['data_path']) as f:
    data = json.load(f)

exam = data['exam_result']
profile = data['student_profile']
weak = data['weak_concepts']
trajectory = data['trajectory']
```

## 시험 정보

- **학생**: {{< student_name >}}
- **시험 일자**: `{python} exam['exam_date']`
- **총 점수**: `{python} exam['final_score']`점

## 성적 분석

```{python}
#| fig-cap: "과목별 점수"
#| fig-width: 8
#| fig-height: 4

# 과목별 점수 막대그래프
subjects = exam['subject_scores'].keys()
scores = exam['subject_scores'].values()

plt.figure(figsize=(8, 4))
plt.bar(subjects, scores)
plt.xlabel('과목')
plt.ylabel('점수')
plt.title('과목별 점수')
plt.ylim(0, 100)
plt.grid(axis='y', alpha=0.3)
plt.savefig('subject_scores.png', bbox_inches='tight', dpi=300)
plt.show()
```

## 취약 개념

```{python}
#| tbl-cap: "취약 개념 분석"

# 취약 개념 테이블
weak_df = pd.DataFrame(weak)
weak_df['정답률'] = (weak_df['accuracy'] * 100).round(1).astype(str) + '%'
print(weak_df[['name', '정답률', 'total_attempts']].to_markdown(index=False))
```

## 학습 추세

```{python}
#| fig-cap: "능력치 변화 추이"
#| fig-width: 8
#| fig-height: 4

# 시계열 그래프
history = trajectory['historical_data']
dates = [h['date'] for h in history]
thetas = [h['theta'] for h in history]

plt.figure(figsize=(8, 4))
plt.plot(dates, thetas, marker='o')
plt.xlabel('날짜')
plt.ylabel('능력치 (θ)')
plt.title('능력치 변화 추이')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('theta_trajectory.png', bbox_inches='tight', dpi=300)
plt.show()
```

## 개인화 코멘트

`{python} generate_personalized_feedback(profile['student_id'], exam['id'])`
```

---

## 구현 예시

### FastAPI 엔드포인트

```python
from fastapi import FastAPI, Request, BackgroundTasks
from governance.backend import require_policy

app = FastAPI()

@app.get("/api/analytics/student/{student_id}/profile")
@require_policy("dreamseedai.analytics.view_profile")
async def get_student_analytics_profile(
    request: Request,
    student_id: str
):
    """
    학생 분석 프로파일 조회
    
    정책 검증:
    - 교사: 자기 반 학생만
    - 학생: 본인만
    - 학부모: 자녀만
    """
    profile = await db.fetch_one(
        "SELECT * FROM student_profiles WHERE student_id = $1",
        student_id
    )
    
    trajectory = await estimate_ability_trajectory(student_id)
    weak_concepts = await identify_weak_concepts(student_id)
    
    return {
        "profile": dict(profile),
        "trajectory": trajectory,
        "weak_concepts": weak_concepts
    }

@app.post("/api/analytics/generate-report")
@require_policy("dreamseedai.analytics.generate_report")
async def generate_report_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    student_id: str,
    exam_id: str,
    output_format: str = "pdf"
):
    """
    리포트 생성
    
    정책 검증:
    - 교사 또는 학생/학부모만 가능
    """
    # 비동기 백그라운드 작업으로 리포트 생성
    background_tasks.add_task(
        generate_exam_report,
        student_id,
        exam_id,
        output_format
    )
    
    return {"status": "generating", "message": "리포트 생성 중입니다"}
```

---

## 기술 스택

### 프로그래밍 언어

- **Python**: 데이터 분석, AI 모델
- **R**: 통계 분석, 리포트 생성

### 머신러닝 프레임워크

- **TensorFlow**: 딥러닝 모델
- **PyTorch**: 연구용 모델
- **scikit-learn**: 전통적인 ML 알고리즘

### 통계 분석 도구

- **R**: 고급 통계 분석
- **SciPy**: 과학 계산
- **NumPy**: 수치 연산
- **statsmodels**: 통계 모델링

### 리포트 생성 도구

- **Quarto**: 현대적인 문서 생성
- **RMarkdown**: R 기반 리포트
- **Matplotlib/Seaborn**: 데이터 시각화
- **Plotly**: 인터랙티브 그래프

### 데이터 파이프라인

- **Apache Airflow**: 배치 작업 스케줄링
- **Celery**: 비동기 작업 큐
- **Pandas**: 데이터 처리
- **Parquet**: 데이터 저장

---

## 거버넌스 통합

분석 엔진은 거버넌스 계층과 통합되어 데이터 접근 정책을 준수합니다.

### 데이터 접근 제어

```python
@app.get("/api/analytics/class/{class_id}/summary")
@require_policy("dreamseedai.analytics.view_class_summary")
async def get_class_analytics_summary(request: Request, class_id: str):
    """
    학급 통계 조회
    
    정책 검증:
    - 해당 학급 담당 교사만 조회 가능
    - 학생 개인정보는 마스킹
    """
    # ... (구현 생략)
```

**상세 예시**: [거버넌스 통합 예시](../governance-integration/examples.md#데이터-접근-제어)

---

## 가치

DreamSeedAI의 학습 분석 및 리포팅 엔진은:

- ✅ 학생들의 학습 성과를 향상시킵니다
- ✅ 데이터 기반 의사 결정을 지원합니다
- ✅ 교사와 학부모에게 유용한 정보를 제공합니다
- ✅ 개인화된 학습 경험을 가능하게 합니다
- ✅ 문항 품질을 지속적으로 개선합니다

---

## 참조 문서

- **시스템 계층 홈**: [../README.md](../README.md)
- **평가 엔진**: [assessment-engine.md](assessment-engine.md)
- **콘텐츠 관리**: [content-management.md](content-management.md)
- **아키텍처 개요**: [../architecture/overview.md](../architecture/overview.md)
- **거버넌스 통합**: [../governance-integration/examples.md](../governance-integration/examples.md)
