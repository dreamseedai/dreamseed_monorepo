# Phase 2: Adaptive Testing & IRT Engine (CAT)

**시작일**: 2025년 1월  
**상태**: ✅ 완료

---

## 🎯 Phase 2 목표

**적응형 평가 시스템 (Computer Adaptive Testing)**
- IRT (Item Response Theory) 3PL 모델 구현
- CAT (Computerized Adaptive Testing) 엔진
- 문항 은행 (Item Bank) 시스템
- 실시간 능력치(θ) 추정

---

## 📁 Phase 2 구조

```
ops/phase2/
├── README.md                      # 이 파일
├── implementation/                # 구현 문서
│   ├── ITEM_MODELS.md            → backend/ITEM_MODELS_IMPLEMENTATION.md
│   └── ADAPTIVE_EXAM_ROUTER.md   → backend/ADAPTIVE_EXAM_ROUTER_IMPLEMENTATION.md
└── tests/                         # 테스트 (심볼릭 링크)
    ├── test_adaptive_exam_e2e.py → backend/tests/
    └── test_item_models.py       → backend/tests/
```

---

## ✅ 완료된 작업

### IRT/CAT 시스템 구현

#### Phase 1: Schema Verification (INTEGER-based core entities)
**상태**: ✅ 완료

**구현 내용**:
- 기본 데이터베이스 스키마
- 핵심 엔티티 모델
- INTEGER 기반 ID 시스템

---

#### Phase 2: Classes Router (3 endpoints, 10 tests)
**상태**: ✅ 완료

**구현 내용**:
- 학급 관리 API
- 선생님-학생 관계
- 3개 엔드포인트
- 10개 테스트

**파일**:
- `backend/app/api/classes.py`
- `backend/tests/test_classes_router.py`

---

#### Phase 3: IRT/CAT Engine (3PL model, 27 tests)
**상태**: ✅ 완료

**구현 내용**:
- **3PL (Three-Parameter Logistic) 모델**
  - `a`: Discrimination (변별도)
  - `b`: Difficulty (난이도)
  - `c`: Guessing (추측도)
- **CAT 알고리즘**
  - Maximum Information Selection
  - θ (theta) 능력치 추정
  - Standard Error 계산
- **27개 테스트 케이스**

**파일**:
- `backend/app/core/services/exam_engine.py`
- `backend/tests/test_exam_engine.py`

**수학적 기반**:
```
P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))

where:
  θ = 학생 능력치
  a = 문항 변별도 (0.5-2.5)
  b = 문항 난이도 (-3 to +3)
  c = 추측 확률 (0-0.3)
```

---

#### Phase 4: Item Models (4 models, 17 tests)
**상태**: ✅ 완료

**구현 내용**:

**1. Item Model** (문항)
- IRT 파라미터 (a, b, c)
- 문항 내용 (question_text, correct_answer, explanation)
- 주제/분류 (topic, meta)
- `to_engine_format()` 메서드

**2. ItemChoice Model** (선택지)
- 객관식 선택지 관리
- 정답 표시
- item_id와 CASCADE 연결

**3. ItemPool Model** (문항 풀)
- 문항 그룹화 (학년, 과목)
- 시험 설정 (max_items, time_limit)
- Many-to-Many 관계

**4. ItemPoolMembership** (연결 테이블)
- Item ↔ ItemPool 연결
- 순서 관리 (order_num)

**테스트**:
- `backend/tests/test_item_models.py` (17 cases)

---

#### Phase 5: Adaptive Exam Router (5 endpoints, E2E tests)
**상태**: ✅ 완료

**구현 내용**:

**API 엔드포인트**:
1. `POST /api/adaptive/start` - 시험 시작
2. `GET /api/adaptive/next` - 다음 문항 선택
3. `POST /api/adaptive/answer` - 답안 제출 & θ 업데이트
4. `GET /api/adaptive/status` - 시험 상태 조회
5. `POST /api/adaptive/end` - 시험 종료

**주요 기능**:
- 실시간 θ 추정
- 최대 정보량 기준 문항 선택
- 중복 문항 방지
- 시험 진행 상태 추적

**파일**:
- `backend/app/api/adaptive.py`
- `backend/tests/test_adaptive_exam_e2e.py`

---

## 📊 전체 통계

**구현 완료**:
- ✅ 4개 Phase 완료
- ✅ 4개 데이터 모델 (Item, ItemChoice, ItemPool, ItemPoolMembership)
- ✅ 5개 API 엔드포인트
- ✅ 54개 테스트 (100% 통과)
  - IRT Engine: 27 tests ✅
  - Classes Router: 10 tests ✅
  - Item Models: 17 tests ✅
  - Adaptive Router: E2E tests ✅

**시스템 능력**:
1. ✅ 문항 생성 및 관리
2. ✅ IRT 파라미터 기반 난이도 조정
3. ✅ 실시간 능력치 추정
4. ✅ 적응형 문항 선택
5. ✅ 문항 풀 관리
6. ✅ 시험 세션 추적

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    학생 (Student)                        │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP/REST API
                    ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI - Adaptive Router                     │
│  POST /api/adaptive/start   (시험 시작)                  │
│  GET  /api/adaptive/next    (다음 문항)                  │
│  POST /api/adaptive/answer  (답안 제출)                  │
│  GET  /api/adaptive/status  (진행 상태)                  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│            IRT/CAT Engine (3PL Model)                   │
│  - θ (theta) 추정                                        │
│  - Maximum Information Selection                        │
│  - Standard Error 계산                                   │
│  - 문항 정보 함수 I(θ)                                   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Database                        │
│  - items (문항 + IRT 파라미터)                           │
│  - item_choices (선택지)                                 │
│  - item_pools (문항 풀)                                  │
│  - item_pool_membership (연결)                          │
│  - exam_sessions (시험 세션)                            │
│  - attempts (학생 응답)                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 IRT 3PL 모델 상세

### Item Response Function
```python
def probability_correct(theta, a, b, c):
    """
    3PL 모델: 학생이 문항을 맞출 확률
    
    Parameters:
    -----------
    theta : float
        학생 능력치 (-∞ to +∞, 보통 -3 to +3)
    a : float
        문항 변별도 (0.5 to 2.5)
        높을수록 능력치에 따른 정답률 차이가 큼
    b : float
        문항 난이도 (-3 to +3)
        θ = b일 때 정답률 50% (추측 무시 시)
    c : float
        추측 파라미터 (0 to 0.3)
        무작위 추측으로 맞출 확률
    
    Returns:
    --------
    float : 정답 확률 (0 to 1)
    """
    return c + (1 - c) / (1 + np.exp(-a * (theta - b)))
```

### Information Function
```python
def item_information(theta, a, b, c):
    """
    문항 정보 함수: 특정 능력치에서 문항이 제공하는 정보량
    
    CAT는 I(θ)가 최대인 문항을 선택
    """
    P = probability_correct(theta, a, b, c)
    Q = 1 - P
    dP_dtheta = a * (P - c) * Q / (1 - c)
    return (dP_dtheta ** 2) / (P * Q)
```

---

## 🧪 테스트 시나리오

### E2E Test: Complete Adaptive Exam Flow
```python
1. POST /api/adaptive/start
   → exam_session_id 생성
   → 초기 θ = 0.0

2. Loop (20 items):
   GET /api/adaptive/next
   → Maximum Information 기준 문항 선택
   → 중복 방지
   
   POST /api/adaptive/answer
   → 정답 여부 확인
   → θ 업데이트 (MLE)
   → SE(θ) 계산

3. GET /api/adaptive/status
   → current_theta
   → standard_error
   → items_completed
   → is_complete

4. POST /api/adaptive/end
   → final_theta
   → exam_session 종료
```

---

## 📚 관련 문서

### 구현 문서
- [`backend/ITEM_MODELS_IMPLEMENTATION.md`](../../backend/ITEM_MODELS_IMPLEMENTATION.md)
- [`backend/ADAPTIVE_EXAM_ROUTER_IMPLEMENTATION.md`](../../backend/ADAPTIVE_EXAM_ROUTER_IMPLEMENTATION.md)

### 테스트
- [`backend/tests/test_exam_engine.py`](../../backend/tests/test_exam_engine.py)
- [`backend/tests/test_item_models.py`](../../backend/tests/test_item_models.py)
- [`backend/tests/test_adaptive_exam_e2e.py`](../../backend/tests/test_adaptive_exam_e2e.py)

### Phase 관련
- [Phase 0](../phase0/) - 인프라 기초
- [Phase 1](../phase1/) - MVP 출시
- **Phase 2** (현재) - 적응형 평가
- [Security Hardening](../security-hardening/) - 보안 강화 (별도)

---

## 🔬 IRT 이론 참고 자료

1. **Embretson & Reise (2000)**: Item Response Theory for Psychologists
2. **Lord (1980)**: Applications of Item Response Theory to Practical Testing Problems
3. **van der Linden & Hambleton (1997)**: Handbook of Modern Item Response Theory

---

## 🚀 향후 계획 (Phase 3)

### 고급 IRT 기능
- [ ] 4PL 모델 (Upper asymptote)
- [ ] Multidimensional IRT (MIRT)
- [ ] Polytomous models (부분 점수)

### CAT 알고리즘 개선
- [ ] Content balancing (주제별 균형)
- [ ] Exposure control (문항 노출 제어)
- [ ] A-stratification
- [ ] Sympson-Hetter method

### 분석 기능
- [ ] 문항 캘리브레이션 (IRT 파라미터 추정)
- [ ] DIF (Differential Item Functioning) 분석
- [ ] 시험 정보 함수 TIF(θ)
- [ ] 신뢰도 계산

---

**완료일**: 2025년 1월 20일  
**담당**: Backend Team  
**리뷰**: IRT Specialist

**Phase 2 Status**: ✅ **COMPLETE** - All 54 tests passing
