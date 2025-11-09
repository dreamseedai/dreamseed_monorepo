# 평가 엔진 서비스 - 적응형 시험 엔진 (Assessment Engine - SeedTest)

SeedTest는 DreamSeedAI 시스템 계층의 핵심 모듈 중 하나로, 컴퓨터 적응형 테스트(Computerized Adaptive Testing, CAT) 알고리즘을 통해 각 학생에게 개인화된 모의고사를 출제합니다.

## 목차

1. [목표](#목표)
2. [핵심 기술: IRT 모델](#핵심-기술-irt-모델)
3. [적응형 테스트 알고리즘](#적응형-테스트-알고리즘)
4. [기술적 특징](#기술적-특징)
5. [구현 예시](#구현-예시)
6. [거버넌스 통합](#거버넌스-통합)
7. [성능 최적화](#성능-최적화)

---

## 목표

- **정확한 역량 평가**: 학생의 실제 능력 수준을 정확하게 측정합니다.
- **효율적인 시험**: 불필요한 문항 풀이를 줄여 시험 시간을 단축합니다.
- **개인 맞춤 학습 경험**: 학생의 수준에 맞는 난이도의 문항을 제공하여 학습 동기를 유발합니다.
- **다양한 시험 유형 지원**: 고교 과정, SAT, 대학별 고사 등 다양한 시험 유형에 적용 가능하도록 설계합니다.

---

## 핵심 기술: IRT 모델

SeedTest는 **문항 반응 이론 (Item Response Theory, IRT)** 모델을 적용하여 문항 풀 (item bank)의 각 문제에 난이도, 변별도 등의 파라미터를 부여하고, 시험 중 실시간으로 학생의 능력치 (θ)를 추정하면서 최적의 다음 문항을 선택합니다.

### IRT 모델 파라미터

#### 1. 문항 파라미터

| 파라미터 | 기호 | 설명 | 범위 |
|---------|------|------|------|
| **난이도** (Difficulty) | b | 문항의 난이도를 나타내는 값. 값이 클수록 어려운 문항 | -3 ~ +3 |
| **변별도** (Discrimination) | a | 문항이 학생의 능력 수준을 얼마나 잘 구분하는지 나타내는 값 | 0 ~ 2.5 |
| **추측도** (Guessing) | c | 정답을 모르는 학생이 문항을 찍어서 맞힐 확률 | 0 ~ 0.25 |

#### 2. 학생 능력치

| 파라미터 | 기호 | 설명 |
|---------|------|------|
| **능력치** (Ability) | θ (theta) | 학생의 해당 과목에 대한 역량 수준을 나타내는 값. 평균 0, 표준편차 1로 표준화 |

### IRT 3PL 모델

3-Parameter Logistic (3PL) 모델은 가장 일반적으로 사용되는 IRT 모델입니다:

$$
P(θ) = c + \frac{1 - c}{1 + e^{-a(θ - b)}}
$$

여기서:
- $P(θ)$: 능력치 θ를 가진 학생이 문항을 맞힐 확률
- $a$: 변별도 (discrimination)
- $b$: 난이도 (difficulty)
- $c$: 추측도 (guessing)
- $θ$: 학생 능력치

**Python 구현**:
```python
import numpy as np

def irt_3pl_probability(theta: float, a: float, b: float, c: float) -> float:
    """
    IRT 3PL 모델로 정답 확률 계산
    
    Args:
        theta: 학생 능력치
        a: 문항 변별도
        b: 문항 난이도
        c: 문항 추측도
    
    Returns:
        정답 확률 (0~1)
    """
    return c + (1 - c) / (1 + np.exp(-a * (theta - b)))

# 예시
theta = 0.5  # 평균보다 약간 높은 능력
a = 1.2      # 변별도
b = 0.0      # 중간 난이도
c = 0.2      # 20% 추측 확률

prob = irt_3pl_probability(theta, a, b, c)
print(f"정답 확률: {prob:.2%}")  # 약 67%
```

---

## 적응형 테스트 알고리즘

SeedTest는 다음과 같은 방식으로 적응형 테스트를 수행합니다.

### 1. 초기 능력치 추정

학생의 초기 능력치 (θ)를 미리 설정된 평균값 또는 이전 시험 결과를 기반으로 추정합니다.

```python
async def initialize_theta(student_id: str, exam_type: str) -> float:
    """
    학생의 초기 능력치 추정
    
    Args:
        student_id: 학생 ID
        exam_type: 시험 유형 (예: "sat_math", "korean_grammar")
    
    Returns:
        초기 theta 값
    """
    # 이전 시험 결과 조회
    previous_exams = await get_previous_exams(student_id, exam_type)
    
    if previous_exams:
        # 이전 시험의 평균 theta 사용
        theta_history = [exam.final_theta for exam in previous_exams]
        initial_theta = np.mean(theta_history)
    else:
        # 첫 시험: 평균값 (0.0) 사용
        initial_theta = 0.0
    
    return initial_theta
```

### 2. 문항 선택 (Maximum Information)

현재 능력치 추정값을 기반으로 **가장 적절한 문항**을 선택합니다. 일반적으로 **정보량이 최대화되는 문항**을 선택합니다.

#### Fisher Information

문항의 정보량은 Fisher Information으로 측정됩니다:

$$
I(θ) = \frac{a^2 [P'(θ)]^2}{P(θ)[1-P(θ)]}
$$

**Python 구현**:
```python
def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """
    Fisher Information 계산 (문항의 정보량)
    
    Args:
        theta: 현재 능력치 추정값
        a, b, c: 문항 파라미터
    
    Returns:
        정보량 (높을수록 능력 측정에 유용)
    """
    P = irt_3pl_probability(theta, a, b, c)
    Q = 1 - P
    
    # P의 미분
    P_prime = a * (P - c) * Q / (1 - c)
    
    # Fisher Information
    information = (a**2 * P_prime**2) / (P * Q)
    
    return information

async def select_next_item(
    current_theta: float,
    answered_items: list[str],
    item_bank: list[dict],
    content_constraints: dict = None
) -> dict:
    """
    다음 문항 선택 (Maximum Information)
    
    Args:
        current_theta: 현재 능력치 추정값
        answered_items: 이미 푼 문항 ID 리스트
        item_bank: 문항 풀
        content_constraints: 내용 균형 제약 (단원별 비율 등)
    
    Returns:
        선택된 문항
    """
    # 아직 안 푼 문항만 필터링
    available_items = [
        item for item in item_bank 
        if item['id'] not in answered_items
    ]
    
    # 내용 균형 제약 적용
    if content_constraints:
        available_items = apply_content_balancing(
            available_items, 
            answered_items, 
            content_constraints
        )
    
    # 각 문항의 정보량 계산
    item_info = []
    for item in available_items:
        info = fisher_information(
            current_theta,
            item['a'],  # 변별도
            item['b'],  # 난이도
            item['c']   # 추측도
        )
        item_info.append((item, info))
    
    # 정보량이 가장 큰 문항 선택
    best_item = max(item_info, key=lambda x: x[1])[0]
    
    return best_item
```

**예시**: 학생이 중간 난이도 문제를 맞히면 능력 추정치가 올라가고 다음에는 더 어려운 문제를, 틀리면 추정치가 내려가고 좀 더 쉬운 문제를 내는 방식입니다.

### 3. 응답 분석 및 능력치 업데이트

학생의 응답 (정답 또는 오답)을 분석하고, IRT 모델을 사용하여 능력치 추정치를 업데이트합니다.

#### Maximum Likelihood Estimation (MLE)

$$
L(θ) = \prod_{i=1}^{n} P_i(θ)^{u_i} [1-P_i(θ)]^{1-u_i}
$$

여기서 $u_i$는 정답(1) 또는 오답(0)입니다.

**Python 구현**:
```python
from scipy.optimize import minimize_scalar

def log_likelihood(theta: float, responses: list[tuple]) -> float:
    """
    Log-Likelihood 계산
    
    Args:
        theta: 능력치
        responses: [(a, b, c, response), ...] 형태의 응답 리스트
    
    Returns:
        Log-Likelihood (음수)
    """
    ll = 0
    for a, b, c, response in responses:
        P = irt_3pl_probability(theta, a, b, c)
        
        if response == 1:  # 정답
            ll += np.log(P + 1e-10)  # 0 방지
        else:  # 오답
            ll += np.log(1 - P + 1e-10)
    
    return -ll  # 최소화를 위해 음수 반환

async def update_theta_mle(
    current_theta: float,
    responses: list[dict]
) -> tuple[float, float]:
    """
    Maximum Likelihood Estimation으로 theta 업데이트
    
    Args:
        current_theta: 현재 theta
        responses: 응답 이력 [{"a": 1.2, "b": 0.5, "c": 0.2, "response": 1}, ...]
    
    Returns:
        (updated_theta, standard_error)
    """
    # 응답 데이터 변환
    response_data = [
        (r['a'], r['b'], r['c'], r['response'])
        for r in responses
    ]
    
    # MLE 최적화
    result = minimize_scalar(
        lambda theta: log_likelihood(theta, response_data),
        bounds=(-4, 4),
        method='bounded'
    )
    
    updated_theta = result.x
    
    # Standard Error 계산 (Fisher Information의 역수)
    total_info = sum(
        fisher_information(updated_theta, r['a'], r['b'], r['c'])
        for r in responses
    )
    standard_error = 1 / np.sqrt(total_info)
    
    return updated_theta, standard_error
```

#### Bayesian 업데이트 (EAP: Expected A Posteriori)

사전 확률을 활용한 Bayesian 방법:

```python
def bayesian_update_theta(
    current_theta: float,
    prior_mean: float,
    prior_std: float,
    responses: list[dict]
) -> tuple[float, float]:
    """
    Bayesian EAP으로 theta 업데이트
    
    Args:
        current_theta: 현재 theta
        prior_mean: 사전 분포 평균
        prior_std: 사전 분포 표준편차
        responses: 응답 이력
    
    Returns:
        (updated_theta, posterior_std)
    """
    # 사후 확률 계산을 위한 그리드
    theta_grid = np.linspace(-4, 4, 100)
    
    # 사전 확률 (정규분포)
    prior = norm.pdf(theta_grid, prior_mean, prior_std)
    
    # 우도 (likelihood)
    likelihood = np.ones_like(theta_grid)
    for r in responses:
        prob = irt_3pl_probability(theta_grid, r['a'], r['b'], r['c'])
        if r['response'] == 1:
            likelihood *= prob
        else:
            likelihood *= (1 - prob)
    
    # 사후 확률
    posterior = prior * likelihood
    posterior /= np.sum(posterior)  # 정규화
    
    # EAP (기댓값)
    updated_theta = np.sum(theta_grid * posterior)
    
    # 사후 표준편차
    posterior_std = np.sqrt(np.sum((theta_grid - updated_theta)**2 * posterior))
    
    return updated_theta, posterior_std
```

### 4. 반복 (Adaptive Loop)

2번(문항 선택)과 3번(응답 분석) 과정을 종료 기준에 도달할 때까지 반복합니다.

```python
async def run_adaptive_test(
    student_id: str,
    exam_type: str,
    max_items: int = 30,
    se_threshold: float = 0.3
) -> dict:
    """
    적응형 테스트 실행
    
    Args:
        student_id: 학생 ID
        exam_type: 시험 유형
        max_items: 최대 문항 수
        se_threshold: 표준 오차 임계치
    
    Returns:
        시험 결과
    """
    # 1. 초기화
    current_theta = await initialize_theta(student_id, exam_type)
    responses = []
    answered_items = []
    
    # 2. 적응형 루프
    while len(answered_items) < max_items:
        # 2-1. 문항 선택
        next_item = await select_next_item(
            current_theta,
            answered_items,
            item_bank=await get_item_bank(exam_type)
        )
        
        # 2-2. 학생에게 문항 제시 (실제로는 프론트엔드에서 처리)
        # ... (웹소켓 등으로 문항 전송)
        
        # 2-3. 응답 대기 및 수신
        response = await wait_for_student_response(student_id, next_item['id'])
        
        # 2-4. 응답 기록
        responses.append({
            'a': next_item['a'],
            'b': next_item['b'],
            'c': next_item['c'],
            'response': response['is_correct']
        })
        answered_items.append(next_item['id'])
        
        # 2-5. Theta 업데이트
        current_theta, se = await update_theta_mle(current_theta, responses)
        
        # 2-6. 종료 조건 확인
        if se < se_threshold:
            break
    
    # 3. 최종 점수 산출
    final_score = convert_theta_to_score(current_theta, exam_type)
    
    return {
        'student_id': student_id,
        'exam_type': exam_type,
        'final_theta': current_theta,
        'final_score': final_score,
        'items_answered': len(answered_items),
        'standard_error': se
    }
```

### 5. 종료 기준

- **문항 수 한도**: 미리 설정된 문항 수를 모두 풀이하면 시험 종료
- **추정치의 표준 오차 임계치**: 능력치 추정치의 표준 오차가 특정 값 이하로 떨어지면 시험 종료
  - 예: SE < 0.3 (충분히 정확한 추정)

### 6. 최종 능력치 산출 및 점수 환산

시험 종료 시 학생의 최종 능력 추정치를 산출하고, 이를 기존 점수 체계 (예: 100점 만점 또는 등급)로 환산하여 성적을 냅니다.

```python
def convert_theta_to_score(theta: float, exam_type: str) -> float:
    """
    Theta를 점수로 환산
    
    Args:
        theta: 최종 능력치
        exam_type: 시험 유형
    
    Returns:
        환산 점수 (0~100)
    """
    # 시험 유형별 환산 공식
    if exam_type == "sat_math":
        # SAT 수학: 200-800 점
        score = 500 + 100 * theta  # 평균 500, 표준편차 100
        return max(200, min(800, score))
    
    elif exam_type == "korean_grammar":
        # 한국어 문법: 0-100점
        # theta를 정규분포 누적확률로 변환 후 100점 스케일링
        percentile = norm.cdf(theta)
        score = percentile * 100
        return round(score, 2)
    
    else:
        # 기본: 평균 70, 표준편차 10
        score = 70 + 10 * theta
        return max(0, min(100, score))
```

---

## 기술적 특징

### 1. 컴퓨터 적응형 테스트 (CAT)

SeedTest는 수십 년간 GRE, GMAT 등의 시험에 활용되어 온 정교한 CAT 기법을 모의고사와 학습용 테스트에 도입했습니다.

**CAT의 장점**:
- 시험 시간 단축 (평균 30-50% 감소)
- 정확한 능력 측정
- 학생 맞춤형 경험
- 문항 노출 위험 감소

### 2. 실시간 능력치 업데이트

시험 엔진은 매 문제마다 현재까지의 답안을 바탕으로 능력치를 업데이트합니다.

**업데이트 방법**:
- **Maximum Likelihood Estimation (MLE)**: 가장 일반적
- **Bayesian EAP (Expected A Posteriori)**: 사전 확률 활용

### 3. 유연한 설정

시험 종류별 (고교과정, SAT, 대학별고사 등)로 다른 문항 풀과 초기 분포를 사용하도록 설정할 수 있습니다.

```python
# 시험 유형별 설정
EXAM_CONFIGS = {
    "sat_math": {
        "item_bank": "sat_math_items",
        "initial_theta": 0.0,
        "prior_mean": 0.0,
        "prior_std": 1.0,
        "max_items": 30,
        "se_threshold": 0.3,
        "content_balancing": {
            "algebra": 0.30,
            "geometry": 0.25,
            "statistics": 0.25,
            "calculus": 0.20
        }
    },
    "korean_grammar": {
        "item_bank": "korean_grammar_items",
        "initial_theta": 0.0,
        "max_items": 25,
        "se_threshold": 0.35
    }
}
```

### 4. 내용 균형 (Content Balancing)

시험 중 내용 균형 (과목/단원별 문항 비율 등)도 정책에 맞게 고려합니다. 특정 과목 또는 단원에 치우치지 않도록 문항을 선택합니다.

```python
def apply_content_balancing(
    available_items: list[dict],
    answered_items: list[str],
    constraints: dict
) -> list[dict]:
    """
    내용 균형 제약 적용
    
    Args:
        available_items: 사용 가능한 문항 리스트
        answered_items: 이미 푼 문항 ID 리스트
        constraints: 단원별 목표 비율 {"algebra": 0.30, ...}
    
    Returns:
        필터링된 문항 리스트
    """
    # 현재까지 푼 문항의 단원별 비율 계산
    answered_by_topic = {}
    for item_id in answered_items:
        item = get_item_by_id(item_id)
        topic = item['topic']
        answered_by_topic[topic] = answered_by_topic.get(topic, 0) + 1
    
    total_answered = len(answered_items)
    
    # 가장 부족한 단원 찾기
    underrepresented_topics = []
    for topic, target_ratio in constraints.items():
        current_ratio = answered_by_topic.get(topic, 0) / max(total_answered, 1)
        if current_ratio < target_ratio:
            underrepresented_topics.append(topic)
    
    # 부족한 단원의 문항 우선 선택
    if underrepresented_topics:
        filtered = [
            item for item in available_items
            if item['topic'] in underrepresented_topics
        ]
        return filtered if filtered else available_items
    
    return available_items
```

---

## 구현 예시

### FastAPI 엔드포인트

```python
from fastapi import FastAPI, Request, HTTPException
from governance.backend import require_policy

app = FastAPI()

@app.post("/api/exams/start")
@require_policy("dreamseedai.exam.start")
async def start_adaptive_exam(
    request: Request,
    student_id: str,
    exam_type: str
):
    """
    적응형 시험 시작
    
    정책 검증:
    - 학생이 시험 응시 자격이 있는지 확인
    - 시험 시간대 확인
    """
    # 시험 세션 생성
    exam_session = await create_exam_session(
        student_id=student_id,
        exam_type=exam_type
    )
    
    # 초기 theta 설정
    initial_theta = await initialize_theta(student_id, exam_type)
    
    # 첫 문항 선택
    first_item = await select_next_item(
        current_theta=initial_theta,
        answered_items=[],
        item_bank=await get_item_bank(exam_type)
    )
    
    return {
        "session_id": exam_session.id,
        "initial_theta": initial_theta,
        "first_item": first_item
    }

@app.post("/api/exams/{session_id}/submit-answer")
@require_policy("dreamseedai.exam.submit_answer")
async def submit_answer(
    request: Request,
    session_id: str,
    item_id: str,
    answer: str
):
    """
    답안 제출 및 다음 문항 반환
    
    정책 검증:
    - 시험 시간 내인지 확인
    - 해당 세션의 학생인지 확인
    """
    # 세션 정보 조회
    session = await get_exam_session(session_id)
    
    # 답안 채점
    is_correct = await grade_answer(item_id, answer)
    
    # 응답 기록
    await record_response(session_id, item_id, answer, is_correct)
    
    # Theta 업데이트
    responses = await get_all_responses(session_id)
    updated_theta, se = await update_theta_mle(
        session.current_theta,
        responses
    )
    
    # 세션 업데이트
    await update_session_theta(session_id, updated_theta, se)
    
    # 종료 조건 확인
    config = EXAM_CONFIGS[session.exam_type]
    if len(responses) >= config['max_items'] or se < config['se_threshold']:
        # 시험 종료
        final_score = convert_theta_to_score(updated_theta, session.exam_type)
        await finalize_exam(session_id, updated_theta, final_score)
        
        return {
            "status": "completed",
            "final_theta": updated_theta,
            "final_score": final_score,
            "items_answered": len(responses)
        }
    
    # 다음 문항 선택
    next_item = await select_next_item(
        current_theta=updated_theta,
        answered_items=[r['item_id'] for r in responses],
        item_bank=await get_item_bank(session.exam_type)
    )
    
    return {
        "status": "continue",
        "current_theta": updated_theta,
        "standard_error": se,
        "next_item": next_item,
        "progress": len(responses) / config['max_items']
    }
```

---

## 거버넌스 통합

평가 엔진은 거버넌스 계층과 통합되어 정책을 준수합니다.

### 정책 적용 예시

```python
# 시험 부정행위 감지
@app.post("/api/exams/{session_id}/detect-anomaly")
async def detect_exam_anomaly(
    request: Request,
    session_id: str,
    metadata: dict
):
    """시험 중 이상 행동 감지"""
    
    policy_client = get_policy_client()
    
    # 이상 행동 패턴 분석
    result = await policy_client.evaluate(
        "dreamseedai.exam.anomaly_detection",
        {
            "session": await get_exam_session(session_id),
            "metadata": metadata,  # 마우스 이동, 탭 전환 등
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    if not result.get("allow"):
        # 의심스러운 행동 감지
        await flag_exam_session(session_id, result.get("reason"))
        await notify_proctors(session_id, result.get("reason"))
    
    return {"flagged": not result.get("allow")}
```

**상세 예시**: [거버넌스 통합 예시](../governance-integration/examples.md#시험-제출-관리)

---

## 성능 최적화

### 1. 문항 파라미터 캐싱

```python
import redis

redis_client = redis.Redis(host='redis', port=6379)

async def get_item_bank(exam_type: str) -> list[dict]:
    """문항 풀 조회 (캐싱)"""
    
    cache_key = f"item_bank:{exam_type}"
    
    # 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # DB 조회
    items = await db.fetch_all(
        "SELECT * FROM items WHERE exam_type = $1",
        exam_type
    )
    
    # 캐싱 (1시간)
    redis_client.setex(cache_key, 3600, json.dumps(items))
    
    return items
```

### 2. 병렬 정보량 계산

```python
from concurrent.futures import ThreadPoolExecutor

async def select_next_item_optimized(
    current_theta: float,
    available_items: list[dict]
) -> dict:
    """병렬로 정보량 계산하여 문항 선택"""
    
    with ThreadPoolExecutor() as executor:
        # 병렬로 정보량 계산
        futures = [
            executor.submit(
                fisher_information,
                current_theta,
                item['a'],
                item['b'],
                item['c']
            )
            for item in available_items
        ]
        
        # 결과 수집
        item_info = [
            (item, future.result())
            for item, future in zip(available_items, futures)
        ]
    
    # 최대 정보량 문항 선택
    return max(item_info, key=lambda x: x[1])[0]
```

---

## 참조 문서

- **시스템 계층 홈**: [../README.md](../README.md)
- **아키텍처 개요**: [../architecture/overview.md](../architecture/overview.md)
- **거버넌스 통합**: [../governance-integration/examples.md](../governance-integration/examples.md)
- **AI 모델 - IRT**: [../ai-models/irt-model.md](../ai-models/irt-model.md) (작성 예정)
