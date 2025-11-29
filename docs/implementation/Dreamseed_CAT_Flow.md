# DreamSeedAI CAT Flow (IRT 기반 적응형 시험 전체 흐름)

본 문서는 DreamSeedAI의 **적응형 시험(Computerized Adaptive Testing, CAT)**이 실제 시스템 안에서 어떻게 동작하는지,
엔티티/서비스/API/인프라 관점에서 **끝에서 끝까지(End-to-End)** 설명하는 설계 문서입니다.

## 대상 독자

* 백엔드/데이터 엔지니어 (구현/리팩토링 기준)
* 연구/AI 엔지니어 (IRT/CAT 알고리즘 검토)
* 아키텍트/리드 (전체 흐름 및 품질/확장성 검토)

## 연관 파일

* `backend/app/models/core_models_expanded.py` – ExamSession, Attempt, Item 등 ORM
* `backend/app/services/exam_engine.py` – AdaptiveEngine 및 IRT 계산 로직
* `backend/app/services/item_bank.py` – ItemBankService (문항 조회/필터링/랭킹)
* `backend/app/api/routers/adaptive_exam.py` – /api/adaptive/* 라우터
* `docs/implementation/Dreamseed_Core_Schema_Alignment.md` – 스키마 설계 가이드
* `docs/implementation/ADAPTIVE_TESTING_INTEGRATION_GUIDE.md` – 통합 가이드

---

## 1. 개념 요약

### 1.1 핵심 개념

* **θ (theta)**: 학생 능력치 (IRT 능력 추정 값, 보통 -3 ~ +3 범위)
* **SE (Standard Error)**: θ 추정값의 표준 오차 (작을수록 신뢰도 높음)
* **a, b, c**: IRT 3PL 문항 파라미터
  * **a**: 변별도 (discrimination) - 문항이 능력 차이를 얼마나 잘 구분하는가
  * **b**: 난이도 (difficulty) - 50% 정답 확률을 가지는 능력 수준
  * **c**: 추측도 (guessing) - 능력이 매우 낮아도 맞힐 확률 (보통 0.2~0.25)
* **정보 함수 (Fisher Information)**: 특정 θ에서 해당 문항이 주는 정보량
  * 정보량이 큰 문항 = 현재 학생 능력에 가장 적합한 문항

### 1.2 IRT 3PL 모델

```
P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))

여기서:
- P(θ): 능력 θ인 학생이 정답할 확률
- a: 변별도 (높을수록 능력에 따라 확률 급변)
- b: 난이도 (문항의 어려움 정도)
- c: 추측도 (최소 정답 확률)
```

### 1.3 DreamSeedAI CAT의 목표

* **짧은 문항 수로 높은 측정 정확도** (정확한 θ 추정)
* **학생 능력에 맞는 난이도로 스트레스/무력감 감소**
* **시험 후 즉각적인 분석과 추천으로 학습 선순환 형성**

---

## 2. 전체 흐름 개요 (High-Level)

시험 1회(ExamSession)의 전체 흐름은 다음 단계로 구성됩니다:

```
1. START    → ExamSession 생성 + AdaptiveEngine 초기화 (θ=0.0)
2. LOOP     ↓
   ├─ NEXT  → ItemBank에서 후보 문항 로딩 + 정보량 최대 문항 선택
   ├─ SOLVE → 학생이 문항 풀이 (프론트엔드)
   └─ ANSWER → Attempt 저장 + θ/SE 업데이트 + 종료 조건 검사
3. TERMINATE → ExamSession.status = 'completed' + 결과 저장
4. REPORT   → 리포트/추천/튜터 연계
```

### 2.1 시퀀스 다이어그램

```
학생                FastAPI Router          ItemBankService       AdaptiveEngine      Database
 │                        │                        │                     │                │
 ├─ POST /start ────────→ │                        │                     │                │
 │                        ├─ CREATE ExamSession ───────────────────────────────────────→ │
 │                        ├─ NEW AdaptiveEngine ───────────────────────→ │                │
 │                        ├─ CACHE engine ─────────┘                     │                │
 │ ←── exam_session_id ───┤                        │                     │                │
 │                        │                        │                     │                │
 ├─ GET /next ──────────→ │                        │                     │                │
 │                        ├─ GET exam_session ─────────────────────────────────────────→ │
 │                        ├─ GET engine from cache │                     │                │
 │                        ├─ get_candidate_items ─→ │                     │                │
 │                        │                        ├─ load_unattempted ──────────────→ │
 │                        │                        ├─ filter_by_difficulty               │
 │                        │                        ├─ rank_by_information                │
 │                        │ ←── ranked_items ──────┤                     │                │
 │                        ├─ pick_best_item ───────→                     │                │
 │ ←── item_id + θ ───────┤                        │                     │                │
 │                        │                        │                     │                │
 ├─ (solve problem) ──────┘                        │                     │                │
 │                        │                        │                     │                │
 ├─ POST /answer ───────→ │                        │                     │                │
 │    (item_id, correct)  │                        │                     │                │
 │                        ├─ GET item params ──────────────────────────────────────────→ │
 │                        ├─ record_attempt ───────────────────────────→ │                │
 │                        │                        │                     ├─ update_theta │
 │                        │                        │                     ├─ calc SE      │
 │                        │ ←── new θ, SE ─────────────────────────────┤                │
 │                        ├─ CREATE Attempt ───────────────────────────────────────────→ │
 │                        ├─ UPDATE ExamSession (θ, SE) ───────────────────────────────→ │
 │                        ├─ should_stop? ─────────────────────────────→ │                │
 │                        │ ←── true/false ────────────────────────────┤                │
 │ ←── θ, SE, completed ──┤                        │                     │                │
 │                        │                        │                     │                │
 (if not completed, repeat from /next)
 │                        │                        │                     │                │
 (if completed)           │                        │                     │                │
 │                        ├─ UPDATE status='completed' ────────────────────────────────→ │
 │                        ├─ CALCULATE score ──────┘                     │                │
 │                        ├─ CLEAR cache ──────────┘                     │                │
 │ ←── final summary ─────┤                        │                     │                │
```

---

## 3. 엔티티 및 테이블 구조 요약

### 3.1 핵심 테이블

#### organizations
```sql
id              INTEGER PRIMARY KEY
name            VARCHAR(255)
type            VARCHAR(50)
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

#### users
```sql
id              INTEGER PRIMARY KEY
org_id          INTEGER → organizations.id
email           VARCHAR(255) UNIQUE
password_hash   VARCHAR(255)
role            VARCHAR(20)  -- student/teacher/parent/admin
is_active       BOOLEAN
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

#### students
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER → users.id (UNIQUE)
org_id          INTEGER → organizations.id
grade           VARCHAR(20)
birth_year      INTEGER
locale          VARCHAR(20)
meta            JSON
created_at      TIMESTAMP
```

#### items (문항)
```sql
id              BIGINT PRIMARY KEY
topic           VARCHAR(255)
a               NUMERIC(6,3)  -- 변별도 (discrimination)
b               NUMERIC(6,3)  -- 난이도 (difficulty)
c               NUMERIC(6,3)  -- 추측도 (guessing)
question_text   TEXT
explanation     TEXT
meta            JSON          -- choices, subject, skill_tags, etc.
```

#### exam_sessions (시험 세션)
```sql
id              BIGINT PRIMARY KEY
student_id      INTEGER → students.id
class_id        INTEGER → classes.id (nullable)
exam_type       VARCHAR(50)   -- placement/practice/final
status          VARCHAR(20)   -- in_progress/completed/abandoned
started_at      TIMESTAMP
ended_at        TIMESTAMP
theta           NUMERIC(6,3)  -- 최종 능력 추정치
standard_error  NUMERIC(6,3)  -- 표준 오차
score           NUMERIC(5,2)  -- 백분율 점수
duration_sec    INTEGER
meta            JSON          -- max_items, termination_reason, etc.
```

#### attempts (문항별 응답)
```sql
id                BIGINT PRIMARY KEY
student_id        INTEGER → students.id
exam_session_id   BIGINT → exam_sessions.id
item_id           BIGINT → items.id
correct           BOOLEAN
submitted_answer  TEXT
selected_choice   INTEGER
response_time_ms  INTEGER
created_at        TIMESTAMP
meta              JSON      -- theta_before, theta_after, etc.
```

### 3.2 관계도

```
Organization 1───N User 1───1 Student
                                  │
                                  │ N
                                  ↓
                            ExamSession
                                  │
                                  │ 1
                                  ↓ N
                              Attempt ───N→1 Item
```

---

## 4. 서비스 계층 구성

### 4.1 AdaptiveEngine (`backend/app/services/exam_engine.py`)

**역할**: IRT 계산 및 적응형 로직의 핵심 엔진

**핵심 함수**:
```python
# IRT 3PL 확률 계산
irt_probability(a: float, b: float, c: float, theta: float) -> float

# Fisher 정보 함수
item_information(a: float, b: float, c: float, theta: float) -> float

# MLE 기반 θ 업데이트 (Newton-Raphson)
update_theta_mle(
    theta: float,
    item_params: List[Dict],
    responses: List[bool],
    max_iter: int = 10
) -> float

# EAP 기반 θ 업데이트 (Bayesian)
update_theta_eap(
    item_params: List[Dict],
    responses: List[bool],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0
) -> Tuple[float, float]
```

**클래스 인터페이스**:
```python
class AdaptiveEngine:
    def __init__(self, initial_theta: float = 0.0, max_items: int = 20):
        self.theta = initial_theta
        self.max_items = max_items
        self.item_history: List[Dict] = []
        self.response_history: List[bool] = []
    
    def record_attempt(self, item_id: int, params: Dict, correct: bool) -> Dict:
        """문항 응답 기록 및 θ 업데이트"""
    
    def pick_item(self, available_items: List[Dict]) -> Optional[Dict]:
        """최대 정보량 문항 선택"""
    
    def should_stop(self) -> bool:
        """종료 조건 검사 (SE < 0.3 or max_items)"""
    
    def get_session_summary(self) -> Dict:
        """현재 세션 요약 반환"""
```

### 4.2 ItemBankService (`backend/app/services/item_bank.py`)

**역할**: 문항 조회, 필터링, 랭킹 전담

**핵심 메서드**:
```python
class ItemBankService:
    async def load_unattempted_items(
        self,
        exam_session_id: int,
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Item]:
        """아직 시도하지 않은 문항 로딩"""
    
    def filter_by_difficulty(
        self,
        items: List[Item],
        theta: float,
        window: float = 1.0
    ) -> List[Dict]:
        """난이도 윈도우 필터링: |b - θ| ≤ window"""
    
    def rank_by_information(
        self,
        theta: float,
        items: List[Dict]
    ) -> List[Dict]:
        """Fisher 정보량 기준 정렬"""
    
    async def get_candidate_items(
        self,
        exam_session_id: int,
        theta: float,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_window: float = 1.0
    ) -> List[Dict]:
        """통합 파이프라인: load → filter → rank"""
    
    def pick_best_item(self, ranked_items: List[Dict]) -> Optional[Dict]:
        """최상위 문항 선택"""
```

**처리 파이프라인**:
```
DB Items
   ↓
[1] Exclude Attempted Items (exam_session_id)
   ↓
[2] Filter by Subject/Topic (optional)
   ↓
[3] Filter by Difficulty Window (|b - θ| ≤ 1.0)
   ↓
[4] Calculate Information for each item
   ↓
[5] Sort by Information (descending)
   ↓
[6] Pick Best Item (or apply exposure control)
   ↓
Selected Item
```

### 4.3 Adaptive Exam Router (`backend/app/api/routers/adaptive_exam.py`)

**역할**: HTTP API 레이어, 인증 및 세션 관리

**엔드포인트**:

| Method | Endpoint | 기능 |
|--------|----------|------|
| POST | `/api/adaptive/start` | 시험 시작, ExamSession 생성 |
| GET | `/api/adaptive/next` | 다음 문항 요청 |
| POST | `/api/adaptive/answer` | 답안 제출 및 θ 업데이트 |
| GET | `/api/adaptive/status` | 세션 상태 조회 |
| POST | `/api/adaptive/complete` | 수동 종료 |

---

## 5. API 플로우 상세

### 5.1 시험 시작 – `POST /api/adaptive/start`

**Request**:
```json
{
  "exam_type": "placement",
  "class_id": 1,
  "initial_theta": 0.0,
  "max_items": 20
}
```

**처리 로직**:
1. ✅ 인증 확인: `current_user.role == 'student'`
2. ✅ Student 레코드 조회 (`user_id` 기준)
3. ✅ Class 유효성 검증 (선택사항)
4. ✅ ExamSession 생성:
   ```python
   ExamSession(
       student_id=student.id,
       class_id=class_id,
       exam_type=exam_type,
       status="in_progress",
       started_at=datetime.utcnow(),
       theta=Decimal("0.0"),
       standard_error=Decimal("999.0"),
       meta={"max_items": 20, "initial_theta": 0.0}
   )
   ```
5. ✅ AdaptiveEngine 초기화 및 캐싱:
   ```python
   engine = AdaptiveEngine(initial_theta=0.0, max_items=20)
   ENGINE_CACHE[exam_session_id] = engine
   ```

**Response**:
```json
{
  "exam_session_id": 123,
  "status": "in_progress",
  "message": "Adaptive exam started successfully",
  "initial_theta": 0.0,
  "max_items": 20
}
```

---

### 5.2 다음 문항 요청 – `GET /api/adaptive/next?exam_session_id=123`

**처리 로직**:

```python
# 1. ExamSession 로딩 및 권한 확인
exam_session = db.query(ExamSession).filter(
    ExamSession.id == exam_session_id,
    ExamSession.student.user_id == current_user.id
).first()

# 2. 상태 확인
if exam_session.status != "in_progress":
    return {"completed": True, "message": "Exam already finished"}

# 3. AdaptiveEngine 복원 (캐시 없으면 DB에서)
engine = ENGINE_CACHE.get(exam_session_id) or restore_engine(exam_session)

# 4. ItemBank 사용하여 후보 문항 획득
bank = ItemBankService(db)
candidates = await bank.get_candidate_items(
    exam_session_id=exam_session_id,
    theta=float(exam_session.theta),
    difficulty_window=1.5
)

# 5. 최적 문항 선택
best_item = bank.pick_best_item(candidates)

if not best_item:
    # 문항 소진 → 강제 종료
    exam_session.status = "completed"
    exam_session.ended_at = datetime.utcnow()
    db.commit()
    return {"completed": True, "message": "No items available"}

# 6. Item 상세 정보 로딩
item = db.query(Item).filter(Item.id == best_item["id"]).first()
```

**Response**:
```json
{
  "completed": false,
  "item": {
    "id": 42,
    "topic": "algebra_linear_equations",
    "question_text": "Solve for x: 3x + 5 = 14",
    "meta": {
      "choices": ["x = 2", "x = 3", "x = 4", "x = 9"],
      "correct_choice": 1
    }
  },
  "current_theta": 0.0,
  "standard_error": 999.0,
  "items_completed": 0,
  "max_items": 20
}
```

**중요**: IRT 파라미터 (a, b, c)는 프론트엔드에 노출하지 않음 (백엔드만 사용)

---

### 5.3 답안 제출 – `POST /api/adaptive/answer`

**Request**:
```json
{
  "exam_session_id": 123,
  "item_id": 42,
  "correct": true,
  "selected_choice": 1,
  "response_time_ms": 15000
}
```

**처리 로직**:

```python
# 1. ExamSession 및 권한 확인
exam_session = validate_session(exam_session_id, current_user)

# 2. Item 로딩 (IRT 파라미터)
item = db.query(Item).filter(Item.id == item_id).first()
params = {"a": float(item.a), "b": float(item.b), "c": float(item.c)}

# 3. AdaptiveEngine에 응답 기록 → θ 업데이트
engine = get_or_restore_engine(exam_session_id, exam_session)
result = engine.record_attempt(
    item_id=item_id,
    params=params,
    correct=correct
)
# result = {
#     "theta": 0.523,
#     "standard_error": 0.892,
#     "items_completed": 1
# }

# 4. Attempt 레코드 생성
attempt = Attempt(
    student_id=exam_session.student_id,
    exam_session_id=exam_session_id,
    item_id=item_id,
    correct=correct,
    selected_choice=selected_choice,
    response_time_ms=response_time_ms,
    created_at=datetime.utcnow(),
    meta={
        "theta_before": float(exam_session.theta),
        "theta_after": result["theta"]
    }
)
db.add(attempt)

# 5. ExamSession 업데이트
exam_session.theta = Decimal(str(result["theta"]))
exam_session.standard_error = Decimal(str(result["standard_error"]))

# 6. 종료 조건 검사
should_terminate = engine.should_stop()

if should_terminate:
    exam_session.status = "completed"
    exam_session.ended_at = datetime.utcnow()
    exam_session.duration_sec = (
        exam_session.ended_at - exam_session.started_at
    ).total_seconds()
    
    # 점수 계산 (정답률)
    all_attempts = db.query(Attempt).filter(
        Attempt.exam_session_id == exam_session_id
    ).all()
    correct_count = sum(1 for a in all_attempts if a.correct)
    score = (correct_count / len(all_attempts)) * 100
    exam_session.score = Decimal(str(score))
    
    # 종료 사유 기록
    if result["standard_error"] < 0.3:
        termination_reason = "standard_error_threshold"
    elif result["items_completed"] >= engine.max_items:
        termination_reason = "max_items_reached"
    else:
        termination_reason = "other"
    
    exam_session.meta["termination_reason"] = termination_reason
    
    # 캐시 정리
    ENGINE_CACHE.pop(exam_session_id, None)

db.commit()
```

**Response**:
```json
{
  "attempt_id": 456,
  "correct": true,
  "theta": 0.523,
  "standard_error": 0.892,
  "items_completed": 1,
  "max_items": 20,
  "completed": false,
  "termination_reason": null
}
```

**종료 시 Response**:
```json
{
  "attempt_id": 478,
  "correct": false,
  "theta": 0.452,
  "standard_error": 0.285,
  "items_completed": 12,
  "max_items": 20,
  "completed": true,
  "termination_reason": "standard_error_threshold"
}
```

---

## 6. 종료 조건 및 정책

### 6.1 기본 종료 조건

`AdaptiveEngine.should_stop()` 구현:

```python
def should_stop(self) -> bool:
    """
    종료 조건:
    1. SE < 0.3 (충분히 정확한 추정)
    2. items_completed >= max_items (최대 문항 수 도달)
    """
    summary = self.get_session_summary()
    
    if summary["standard_error"] < 0.3:
        return True
    
    if summary["items_completed"] >= self.max_items:
        return True
    
    return False
```

### 6.2 확장 가능한 종료 조건

```python
# 시간 제한
if (datetime.utcnow() - exam_session.started_at).seconds > 2700:  # 45분
    termination_reason = "time_limit"
    return True

# θ 변화량 수렴
if abs(current_theta - previous_theta) < 0.05:
    consecutive_stable_count += 1
    if consecutive_stable_count >= 3:
        termination_reason = "theta_converged"
        return True

# 극단적 θ 도달
if abs(theta) > 3.5:
    termination_reason = "extreme_theta"
    return True
```

### 6.3 종료 시 후처리

```python
# 1. ExamSession 종료 표시
exam_session.status = "completed"
exam_session.ended_at = datetime.utcnow()
exam_session.duration_sec = (ended_at - started_at).total_seconds()

# 2. 점수 계산 및 저장
exam_session.score = calculate_score(exam_session)

# 3. 종료 사유 기록
exam_session.meta["termination_reason"] = termination_reason

# 4. 후속 분석 트리거 (비동기)
asyncio.create_task(post_exam_analysis(exam_session_id))

# 5. 캐시 정리
ENGINE_CACHE.pop(exam_session_id)
```

---

## 7. 아키텍처와 확장 포인트

### 7.1 현재 구조의 장점

#### ✅ **서비스 레이어 분리**
```
┌──────────────────────────────────────────┐
│  HTTP Layer (FastAPI Router)            │
│  - 인증/권한                              │
│  - 요청/응답 변환                         │
│  - 세션 관리                              │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴────────┐
       ↓                ↓
┌─────────────┐  ┌──────────────┐
│ ItemBank    │  │ AdaptiveEngine│
│ Service     │  │               │
│ - 문항 조회  │  │ - IRT 계산   │
│ - 필터링    │  │ - θ 추정     │
│ - 랭킹      │  │ - 종료 판단  │
└─────┬───────┘  └──────┬───────┘
      │                 │
      └────────┬────────┘
               ↓
       ┌──────────────┐
       │  ORM Models  │
       │  - Item      │
       │  - Attempt   │
       │  - Session   │
       └──────────────┘
```

#### ✅ **테스트 용이성**
- `AdaptiveEngine`: 순수 함수로 단위 테스트 가능
- `ItemBankService`: Mock DB로 테스트 가능
- `Router`: 통합 테스트로 E2E 검증

#### ✅ **확장성**
- IRT → ML 모델 교체 시 인터페이스만 유지하면 됨
- 노출 제어/콘텐츠 밸런싱은 ItemBank 레벨에서 추가

### 7.2 추후 추가할 기능 후보

#### 1️⃣ **노출 제어 (Exposure Control)**

```python
async def pick_item_with_exposure_control(
    self,
    ranked_items: List[Dict],
    max_exposure: float = 0.2,
    randomization_window: int = 5
) -> Dict:
    """
    특정 문항이 과도하게 출제되는 것을 방지
    
    전략:
    - 상위 N개 문항 중에서 가중 랜덤 선택
    - 노출률이 높은 문항은 선택 확률 감소
    """
    # Redis에서 각 문항의 노출 횟수 조회
    exposure_counts = await get_item_exposure_counts([i["id"] for i in ranked_items])
    
    # 가중치 조정
    weights = []
    for item in ranked_items[:randomization_window]:
        exposure_rate = exposure_counts.get(item["id"], 0) / total_sessions
        penalty = max(0, 1 - exposure_rate / max_exposure)
        weight = item["info"] * penalty
        weights.append(weight)
    
    # 가중 랜덤 선택
    selected = random.choices(ranked_items[:randomization_window], weights=weights)[0]
    
    # 노출 횟수 증가
    await increment_item_exposure(selected["id"])
    
    return selected
```

#### 2️⃣ **콘텐츠 균형 (Content Balancing)**

```python
async def pick_item_with_content_balance(
    self,
    exam_session_id: int,
    ranked_items: List[Dict],
    target_distribution: Dict[str, float]
) -> Dict:
    """
    목표 토픽 분포에 맞춰 문항 선택
    
    예: {"algebra": 0.4, "geometry": 0.3, "statistics": 0.3}
    """
    # 현재까지 출제된 토픽 분포 계산
    current_distribution = await get_topic_distribution(exam_session_id)
    
    # 가장 부족한 토픽 찾기
    deficits = {}
    for topic, target_ratio in target_distribution.items():
        current_ratio = current_distribution.get(topic, 0)
        deficits[topic] = target_ratio - current_ratio
    
    most_needed_topic = max(deficits.items(), key=lambda x: x[1])[0]
    
    # 부족한 토픽의 문항 중 최상위 선택
    for item in ranked_items:
        if item.get("topic") == most_needed_topic:
            return item
    
    # 없으면 일반 최상위 반환
    return ranked_items[0]
```

#### 3️⃣ **적응형 과제 (Adaptive Assignment)**

```python
class AdaptiveAssignmentEngine(AdaptiveEngine):
    """
    연습/숙제용 적응형 엔진
    
    CAT과의 차이점:
    - 종료 조건이 느슨함 (SE < 0.5)
    - 같은 토픽 내에서 난이도만 조정
    - 오답 시 유사 문항 재출제
    """
    def should_stop(self) -> bool:
        return (
            self.standard_error < 0.5 or
            self.items_completed >= self.max_items
        )
    
    def pick_similar_item(self, failed_item: Dict) -> Dict:
        """오답 문항과 유사한 문항 선택"""
        similar_items = find_items_by_skill_tags(
            tags=failed_item["meta"]["skill_tags"],
            difficulty_range=(failed_item["b"] - 0.5, failed_item["b"] + 0.5)
        )
        return random.choice(similar_items)
```

#### 4️⃣ **멀티 모델 지원**

```python
class MultiModelEngine:
    """
    IRT 1PL/2PL/3PL 및 ML 모델 혼용
    """
    def __init__(self, model_type: str = "3PL"):
        if model_type == "1PL":
            self.prob_func = rasch_probability
        elif model_type == "2PL":
            self.prob_func = two_pl_probability
        elif model_type == "3PL":
            self.prob_func = irt_probability
        elif model_type == "ML":
            self.prob_func = neural_irt_probability
    
    def predict_probability(self, theta, item_params):
        return self.prob_func(theta, **item_params)
```

---

## 8. 성능/운영 관점

### 8.1 캐싱 전략

#### 현재: In-Memory Dict
```python
ENGINE_CACHE: Dict[int, AdaptiveEngine] = {}
```

**문제점**:
- 서버 재시작 시 소실
- 멀티 인스턴스에서 공유 불가

#### 개선: Redis 기반 캐싱

```python
import redis
import pickle

redis_client = redis.Redis(host='localhost', port=6379)

def cache_engine(exam_session_id: int, engine: AdaptiveEngine):
    key = f"adaptive_engine:{exam_session_id}"
    value = pickle.dumps(engine)
    redis_client.setex(key, 3600, value)  # 1시간 TTL

def get_cached_engine(exam_session_id: int) -> Optional[AdaptiveEngine]:
    key = f"adaptive_engine:{exam_session_id}"
    value = redis_client.get(key)
    if value:
        return pickle.loads(value)
    return None
```

**장점**:
- 서버 재시작에도 유지
- 로드 밸런서 환경에서도 동작
- TTL로 자동 정리

### 8.2 모니터링 포인트

#### Prometheus 메트릭

```python
from prometheus_client import Counter, Histogram, Gauge

# 시험 세션 수
exam_sessions_total = Counter(
    'dreamseed_exam_sessions_total',
    'Total number of exam sessions',
    ['exam_type', 'status']
)

# 문항 수 분포
items_per_exam = Histogram(
    'dreamseed_items_per_exam',
    'Number of items per exam',
    buckets=[5, 10, 15, 20, 25, 30]
)

# θ 변화량
theta_change = Histogram(
    'dreamseed_theta_change',
    'Theta change per attempt',
    buckets=[-2, -1, -0.5, -0.1, 0, 0.1, 0.5, 1, 2]
)

# 표준오차
standard_error_gauge = Gauge(
    'dreamseed_standard_error',
    'Current standard error',
    ['exam_session_id']
)

# 응답 시간
response_time = Histogram(
    'dreamseed_response_time_seconds',
    'Item response time',
    buckets=[5, 10, 15, 30, 60, 120, 300]
)
```

#### Grafana 대시보드

```yaml
Dashboard: DreamSeed Adaptive Testing

Panels:
  1. Exam Sessions (Time Series)
     - Query: rate(dreamseed_exam_sessions_total[5m])
     - Split by: exam_type, status
  
  2. Items Per Exam (Heatmap)
     - Query: dreamseed_items_per_exam_bucket
  
  3. Theta Distribution (Histogram)
     - Query: dreamseed_theta_change_bucket
  
  4. Average SE (Gauge)
     - Query: avg(dreamseed_standard_error)
  
  5. Response Time P95 (Line)
     - Query: histogram_quantile(0.95, dreamseed_response_time_seconds_bucket)
```

### 8.3 장애/예외 상황 처리

#### 1️⃣ **ItemBank에서 후보 문항 0개**

```python
candidates = await bank.get_candidate_items(exam_session_id, theta)

if not candidates:
    logger.warning(
        f"No candidate items for session {exam_session_id}, theta={theta}"
    )
    
    # 강제 종료
    exam_session.status = "completed"
    exam_session.ended_at = datetime.utcnow()
    exam_session.meta["termination_reason"] = "no_items_available"
    db.commit()
    
    # 관리자 알림
    await send_alert_to_admin(
        title="Item Bank Exhausted",
        message=f"Session {exam_session_id} has no available items"
    )
    
    return {"completed": True, "message": "No items available"}
```

#### 2️⃣ **θ 업데이트 중 수치 불안정**

```python
try:
    new_theta = update_theta_mle(theta, item_params, responses)
except (ValueError, ZeroDivisionError) as e:
    logger.error(f"Theta update failed: {e}")
    
    # 보수적 업데이트 (작은 스텝)
    if correct:
        new_theta = theta + 0.1
    else:
        new_theta = theta - 0.1
    
    # θ 범위 제한
    new_theta = max(-4.0, min(4.0, new_theta))

# 항상 범위 체크
new_theta = np.clip(new_theta, -4.0, 4.0)
```

#### 3️⃣ **Redis 연결 실패**

```python
def get_or_restore_engine(exam_session_id, exam_session):
    try:
        engine = get_cached_engine(exam_session_id)
        if engine:
            return engine
    except redis.ConnectionError:
        logger.warning("Redis connection failed, using fallback")
    
    # Fallback: DB에서 복원
    engine = AdaptiveEngine(
        initial_theta=float(exam_session.theta),
        max_items=exam_session.meta.get("max_items", 20)
    )
    
    # 과거 응답 재생
    attempts = db.query(Attempt).filter(
        Attempt.exam_session_id == exam_session_id
    ).order_by(Attempt.created_at).all()
    
    for attempt in attempts:
        item = db.query(Item).get(attempt.item_id)
        engine.record_attempt(
            item_id=attempt.item_id,
            params={"a": float(item.a), "b": float(item.b), "c": float(item.c)},
            correct=attempt.correct
        )
    
    return engine
```

---

## 9. Phase 0.5 → Phase 1 로드맵

### 9.1 Phase 0.5 (로컬/온프레미스 MVP)

**목표**: 로컬 환경에서 전체 CAT 플로우 동작 검증

**인프라**:
```yaml
Docker Compose:
  - PostgreSQL 14
  - Redis 7
  - FastAPI Backend
  - Prometheus
  - Grafana
  - Backblaze B2 (파일 저장)
```

**체크리스트**:
- [ ] `core_models_expanded.py`를 `core/models.py`로 merge
- [ ] Alembic migration 생성 및 실행
  ```bash
  alembic revision -m "add_adaptive_testing_tables"
  alembic upgrade head
  ```
- [ ] Item 데이터 시딩 (최소 50문항, IRT 파라미터 포함)
  ```bash
  python -m scripts.seed_irt_items
  ```
- [ ] `adaptive_exam` router를 main.py에 등록
  ```python
  from app.api.routers.adaptive_exam import router as adaptive_router
  app.include_router(adaptive_router)
  ```
- [ ] 수동 E2E 테스트
  ```bash
  # 1. 시험 시작
  curl -X POST http://localhost:8001/api/adaptive/start \
    -H "Content-Type: application/json" \
    -d '{"exam_type": "placement", "max_items": 10}'
  
  # 2. 문항 받기
  curl http://localhost:8001/api/adaptive/next?exam_session_id=1
  
  # 3. 답안 제출
  curl -X POST http://localhost:8001/api/adaptive/answer \
    -H "Content-Type: application/json" \
    -d '{"exam_session_id":1,"item_id":5,"correct":true}'
  
  # 4-10. 반복...
  
  # 11. 결과 확인
  curl http://localhost:8001/api/adaptive/status?exam_session_id=1
  ```
- [ ] θ 변화 검증: 정답 → 상승, 오답 → 하강
- [ ] SE 감소 확인: 문항 수 증가 → SE 감소
- [ ] 종료 조건 동작: SE < 0.3 또는 max_items 도달 시 종료

### 9.2 Phase 1 (Cloud + Hybrid)

**목표**: Cloud Run + Cloudflare + 로컬 GPU 하이브리드 구성

**아키텍처**:
```
Internet
   ↓
Cloudflare (CDN + WAF + HTTPS)
   ↓
Cloud Run (FastAPI Backend)
   ├─ Cloud SQL (PostgreSQL)
   ├─ Redis (Memorystore)
   └─ Cloud Storage (파일)
   
로컬 GPU 서버 (별도)
   ├─ LLM Inference (튜터)
   └─ Auto-Grading (채점)
```

**배포 프로세스**:
```bash
# 1. Docker 이미지 빌드
docker build -t gcr.io/dreamseed/backend:latest .

# 2. GCR에 푸시
docker push gcr.io/dreamseed/backend:latest

# 3. Cloud Run 배포
gcloud run deploy dreamseed-backend \
  --image gcr.io/dreamseed/backend:latest \
  --platform managed \
  --region asia-northeast3 \
  --set-env-vars DATABASE_URL=$DB_URL,REDIS_URL=$REDIS_URL \
  --allow-unauthenticated

# 4. Cloudflare에서 도메인 연결
# api.dreamseed.ai → Cloud Run URL
```

**체크리스트**:
- [ ] Cloud SQL 마이그레이션
- [ ] Redis Memorystore 설정
- [ ] Cloud Run 환경 변수 설정
- [ ] Cloudflare DNS 설정
- [ ] 부하 테스트 (동시 100명)
- [ ] 모니터링 대시보드 구성

---

## 10. 품질 보증 체크리스트

### 10.1 기능 테스트

#### ✅ **기본 플로우**
- [ ] 시험 시작 → ExamSession 생성
- [ ] 첫 문항 정상 출제 (θ=0 근처 문항)
- [ ] 정답 제출 → θ 상승
- [ ] 오답 제출 → θ 하강
- [ ] 종료 조건 도달 → status='completed'

#### ✅ **엣지 케이스**
- [ ] 문항 소진 시 강제 종료
- [ ] 동일 문항 중복 출제 방지
- [ ] Redis 장애 시 DB 복원
- [ ] θ가 극단값 도달 시 처리 (-4 ~ +4)
- [ ] 네트워크 지연/타임아웃 처리

#### ✅ **성능**
- [ ] 단일 요청 응답 시간 < 200ms
- [ ] 100 concurrent sessions 동시 처리
- [ ] DB 쿼리 최적화 (N+1 방지)
- [ ] Redis 캐시 hit rate > 90%

### 10.2 알고리즘 검증

#### ✅ **IRT 정확성**
```python
# 시뮬레이션 테스트
def test_irt_simulation():
    true_theta = 1.0
    engine = AdaptiveEngine(initial_theta=0.0)
    
    # 100문항 시뮬레이션
    for i in range(100):
        item = generate_random_item()
        prob = irt_probability(item["a"], item["b"], item["c"], true_theta)
        correct = random.random() < prob
        engine.record_attempt(i, item, correct)
    
    # 수렴 확인
    final_theta = engine.theta
    assert abs(final_theta - true_theta) < 0.2, "Theta did not converge"
```

#### ✅ **문항 선택 효율성**
```python
def test_item_selection_efficiency():
    """정보량 최대 전략이 랜덤보다 효율적인지 검증"""
    
    # 정보량 최대 전략
    adaptive_items_count = simulate_cat(strategy="max_info")
    
    # 랜덤 전략
    random_items_count = simulate_cat(strategy="random")
    
    # CAT이 더 적은 문항으로 목표 SE 도달
    assert adaptive_items_count < random_items_count * 0.7
```

### 10.3 보안 체크

- [ ] 인증된 학생만 자신의 ExamSession 접근
- [ ] IRT 파라미터 (a, b, c) 프론트엔드 노출 금지
- [ ] SQL Injection 방어 (ORM 사용)
- [ ] Rate Limiting (답안 제출 속도 제한)
- [ ] HTTPS 강제 (Cloudflare)

---

## 11. 향후 연구 주제

### 11.1 IRT 고도화

#### **Multidimensional IRT (MIRT)**
- 단일 θ → 다차원 θ (예: 개념 이해도, 계산 능력, 문제 해결력)
- 더 정교한 학생 프로필 구축

#### **Dynamic IRT**
- 시간에 따른 θ 변화 모델링
- 학습 곡선 추적

### 11.2 AI 통합

#### **LLM 기반 문항 생성**
- GPT-4로 자동 문항 생성
- IRT 파라미터 자동 예측 (few-shot learning)

#### **Reinforcement Learning 기반 Item Selection**
- θ 추정 정확도를 reward로 학습
- 최적 문항 시퀀스 발견

### 11.3 교육 효과 검증

#### **A/B 테스트**
- CAT vs 고정 난이도 시험
- 학습 효과 비교 (사전/사후 평가)

#### **사용자 경험 연구**
- 학생 만족도 조사
- 스트레스/동기 수준 측정

---

## 12. 참고 자료

### 12.1 IRT 이론

- [Embretson & Reise (2000). Item Response Theory for Psychologists](https://www.routledge.com/Item-Response-Theory-for-Psychologists/Embretson-Reise/p/book/9780805828191)
- [van der Linden & Hambleton (1997). Handbook of Modern Item Response Theory](https://link.springer.com/book/10.1007/978-1-4757-2691-6)

### 12.2 CAT 구현

- [Magis & Raîche (2012). Random Generation of Response Patterns under CAT](https://www.jstatsoft.org/article/view/v048i08)
- [Chalmers (2012). mirt: Multidimensional IRT in R](https://www.jstatsoft.org/article/view/v048i06)

### 12.3 오픈소스 참고

- [catsim (Python CAT Simulator)](https://github.com/douglasrizzo/catsim)
- [mirt (R package)](https://github.com/philchalmers/mirt)

---

## 13. 요약

DreamSeedAI의 CAT Flow는 다음을 통합한 **엔드투엔드 적응형 시험 시스템**입니다:

### ✅ **수학적 정확성**
- IRT 3PL 모델
- MLE/EAP θ 추정
- Fisher 정보 함수

### ✅ **소프트웨어 아키텍처**
- 서비스 레이어 분리 (Engine / ItemBank / Router)
- ORM 기반 데이터 모델
- RESTful API 설계

### ✅ **운영 가능성**
- Redis 캐싱
- Prometheus/Grafana 모니터링
- 장애 복구 로직

### ✅ **확장성**
- 노출 제어 / 콘텐츠 밸런싱
- 멀티 모델 지원
- ML/AI 통합 준비

이 문서는 다음 용도로 활용됩니다:

1. **개발자 온보딩** - 신규 팀원이 CAT 시스템을 이해하는 기준
2. **기능 리팩토링** - 코드 변경 시 영향 범위 파악
3. **기술 심사** - 투자자/파트너/정부 과제 설명 자료
4. **특허 출원** - 적응형 학습 시스템 기술 명세

---

**작성**: DreamSeedAI 개발팀  
**최종 수정**: 2025-11-20  
**버전**: 1.0.0
