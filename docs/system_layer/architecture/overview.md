# 시스템 계층 - 아키텍처 개요 (Architecture Overview)

DreamSeedAI 시스템 계층의 핵심적인 구조적 특징은 **마이크로서비스 아키텍처**를 채택했다는 점입니다. 이는 여러 가지 기능 (예: 시험 출제 엔진, 학습 분석 엔진, AI 튜터 엔진, 사용자 관리, 콘텐츠 관리 등)이 각각 독립된 서비스로 구현되어 컨테이너화 (Docker 등)되어 배포된다는 것을 의미합니다.

## 목차

1. [마이크로서비스 아키텍처의 장점](#마이크로서비스-아키텍처의-장점)
2. [서비스 간 통신](#서비스-간-통신)
3. [데이터 저장](#데이터-저장)
4. [배포 및 운영](#배포-및-운영)
5. [거버넌스 통합](#거버넌스-통합)
6. [아키텍처 다이어그램](#아키텍처-다이어그램)

---

## 마이크로서비스 아키텍처의 장점

### 1. 확장성 (Scalability)

각 서비스를 독립적으로 확장할 수 있어 사용자 증가에 유연하게 대응할 수 있습니다. 특정 서비스에 트래픽이 집중될 경우, 해당 서비스만 스케일 아웃하여 전체 시스템의 성능 저하를 방지할 수 있습니다.

**예시**:
- **AI 튜터 서비스**: 학습 시간대에 트래픽 증가 → 해당 서비스만 Pod 수 증가
- **시험 제출 서비스**: 시험 마감 시간 전후 → 임시로 인스턴스 추가

**구현**:
```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-tutor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-tutor-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. 유지보수성 (Maintainability)

각 서비스는 독립적으로 개발, 배포, 및 업데이트될 수 있어 유지보수가 용이합니다. 특정 서비스에 문제가 발생하더라도 다른 서비스에는 영향을 미치지 않습니다.

**이점**:
- **독립 배포**: 사용자 관리 서비스 업데이트가 AI 튜터 서비스에 영향 없음
- **팀 자율성**: 각 팀이 서비스별로 독립적으로 개발 가능
- **빠른 반복**: 작은 단위로 배포하여 위험 감소

### 3. 기술 다양성 (Technology Diversity)

각 서비스는 필요에 따라 서로 다른 프로그래밍 언어, 프레임워크, 및 데이터베이스를 사용할 수 있습니다. 이를 통해 각 서비스에 가장 적합한 기술 스택을 선택할 수 있습니다.

**DreamSeedAI 기술 스택 다양성**:

| 서비스 | 언어/프레임워크 | 데이터베이스 | 이유 |
|--------|----------------|-------------|------|
| 사용자 관리 | Python/FastAPI | PostgreSQL | 빠른 개발, 보안 라이브러리 풍부 |
| AI 튜터 | Python/FastAPI | PostgreSQL + Redis | AI/ML 라이브러리 생태계 |
| 데이터 분석 | R/Shiny | PostgreSQL + Parquet | 통계 분석, 시각화 도구 |
| 알림 서비스 | Node.js/Express | Redis | 비동기 I/O, 실시간 처리 |
| 콘텐츠 저장 | MinIO/S3 | 객체 스토리지 | 대용량 미디어 파일 |

### 4. 장애 격리 (Fault Isolation)

한 서비스의 장애가 전체 시스템으로 확산되는 것을 방지합니다. 각 서비스는 독립적으로 운영되므로, 특정 서비스에 문제가 발생하더라도 다른 서비스는 정상적으로 동작할 수 있습니다.

**Circuit Breaker 패턴**:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_ai_tutor_service(query: str):
    """AI 튜터 서비스 호출 (Circuit Breaker 적용)"""
    try:
        response = await httpx.post(
            "http://ai-tutor-service/api/query",
            json={"query": query},
            timeout=5.0
        )
        return response.json()
    except httpx.TimeoutException:
        # 5번 연속 실패 시 Circuit Open → Fallback 응답 반환
        return {"response": "죄송합니다. 일시적으로 서비스를 사용할 수 없습니다."}
```

---

## 서비스 간 통신

### 1. RESTful API

서비스 간 통신은 주로 RESTful API 호출로 이루어집니다.

**특징**:
- 표준 HTTP 프로토콜을 사용하므로, 다양한 프로그래밍 언어 및 플랫폼에서 쉽게 연동할 수 있습니다.
- API Gateway를 통해 인증, 권한 부여, 트래픽 관리, 로깅 등 공통 기능을 제공합니다.

**API Gateway 역할**:
```
클라이언트 요청
    ↓
API Gateway (Kong/Nginx)
    ├─ 인증/인가 (JWT 검증)
    ├─ 속도 제한 (Rate Limiting)
    ├─ 로깅 (Access Log)
    ├─ **거버넌스 정책 적용** ⭐
    └─ 라우팅
        ↓
    ┌────────────────┐
    │  마이크로서비스 │
    └────────────────┘
```

**거버넌스 통합 예시**:
```python
from fastapi import FastAPI, Request
from governance.backend import PolicyEnforcementMiddleware

app = FastAPI()

# API Gateway 역할: 모든 요청에 정책 적용
app.add_middleware(
    PolicyEnforcementMiddleware,
    excluded_paths=["/health", "/metrics"]
)

@app.get("/api/lessons/{lesson_id}")
async def get_lesson(request: Request, lesson_id: str):
    # 정책 미들웨어가 자동으로 검증
    # - 사용자 권한 확인
    # - 접근 시간대 확인
    # - 데이터 보호 정책 확인
    
    lesson = await lesson_service.get(lesson_id)
    return lesson
```

### 2. 메시지 큐 (Message Queue)

일부 비동기 처리가 필요한 부분은 메시지 큐 (예: Apache Kafka, RabbitMQ, Celery 등)를 통해 이벤트를 주고받도록 했습니다.

**예시: 시험 완료 이벤트 처리**

```python
# 시험 서비스 (Publisher)
from kafka import KafkaProducer
import json

async def finish_exam(exam_id: str, student_id: str):
    """시험 완료 처리 및 이벤트 발행"""
    
    # 1. 시험 결과 저장
    result = await exam_service.finalize(exam_id, student_id)
    
    # 2. Kafka 이벤트 발행
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    event = {
        "event_type": "exam_completed",
        "exam_id": exam_id,
        "student_id": student_id,
        "score": result.score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    producer.send('exam-events', value=event)
    producer.flush()
    
    return result
```

```python
# 분석 서비스 (Consumer)
from kafka import KafkaConsumer
import json

def start_analytics_consumer():
    """시험 이벤트를 구독하여 통계 분석 수행"""
    
    consumer = KafkaConsumer(
        'exam-events',
        bootstrap_servers=['kafka:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    for message in consumer:
        event = message.value
        
        if event['event_type'] == 'exam_completed':
            # 비동기 분석 작업 수행
            await analytics_service.analyze_exam_result(
                exam_id=event['exam_id'],
                student_id=event['student_id'],
                score=event['score']
            )
            
            # IRT 모델 업데이트
            await irt_model.update_parameters(
                student_id=event['student_id'],
                exam_id=event['exam_id']
            )
```

**메시지 큐 사용 이점**:
- 서비스 간 결합도 낮춤 (Loose Coupling)
- 비동기 작업 처리 효율화
- 이벤트 기반 아키텍처 (Event-Driven Architecture) 구현
- 재처리 및 에러 핸들링 용이

---

## 데이터 저장

### 1. 관계형 데이터베이스 (PostgreSQL)

중앙의 PostgreSQL 관계형 데이터베이스를 기본으로 사용합니다.

**저장 데이터**:
- 사용자 정보 (students, teachers, admins)
- 학급 정보 (classes, enrollments)
- 시험 문제 (items, exams)
- 학습 기록 (learning_records, submissions)

**장점**:
- 데이터 일관성 및 무결성 보장 (ACID 트랜잭션)
- 복잡한 쿼리 지원 (JOIN, GROUP BY 등)
- 성숙한 생태계 및 도구

**스키마 예시**:
```sql
-- 학생 테이블
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    grade_level INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 학습 기록 테이블
CREATE TABLE learning_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    content_id UUID NOT NULL,
    activity_type VARCHAR(50), -- 'video_watch', 'quiz_solve', 'assignment_submit'
    duration_seconds INTEGER,
    score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (쿼리 성능 최적화)
CREATE INDEX idx_learning_records_student ON learning_records(student_id);
CREATE INDEX idx_learning_records_created_at ON learning_records(created_at DESC);
```

### 2. 캐시 (Redis)

Redis를 사용하여 자주 접근하는 데이터를 캐싱합니다.

**사용 사례**:
- **세션 관리**: JWT 토큰 블랙리스트, 사용자 세션
- **API 응답 캐싱**: 자주 조회되는 콘텐츠, 통계 데이터
- **속도 제한**: Rate limiting 카운터
- **실시간 데이터**: 온라인 사용자 수, 알림 큐

**효과**:
- API 응답 시간 단축 (ms 단위)
- 데이터베이스 부하 감소 (읽기 쿼리 오프로드)

**캐싱 예시**:
```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def cache_result(expire_seconds=300):
    """함수 결과를 Redis에 캐싱하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # 캐시 확인
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 캐시 미스: 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐싱
            redis_client.setex(
                cache_key,
                expire_seconds,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

@cache_result(expire_seconds=600)
async def get_student_statistics(student_id: str):
    """학생 통계 조회 (10분 캐싱)"""
    return await analytics_service.calculate_statistics(student_id)
```

### 3. 분석용 스토리지 (Parquet/Arrow)

데이터 분석 및 리포팅을 위해 Arrow/Parquet 형식으로 데이터를 일시적으로 저장합니다.

**사용 목적**:
- 대용량 데이터 분석 (학습 로그, 통계)
- 데이터 레이크 (Data Lake) 구축
- 데이터 웨어하우스 (Data Warehouse) ETL

**Parquet 장점**:
- 컬럼 기반 저장 (Columnar Storage) → 분석 쿼리 최적화
- 압축률 높음 (저장 공간 절약)
- Apache Spark, Pandas 등과 호환

**예시**:
```python
import pandas as pd
import pyarrow.parquet as pq

async def export_learning_data_to_parquet(date: str):
    """학습 데이터를 Parquet 형식으로 내보내기"""
    
    # PostgreSQL에서 데이터 조회
    query = """
        SELECT student_id, content_id, activity_type, 
               duration_seconds, score, created_at
        FROM learning_records
        WHERE DATE(created_at) = %s
    """
    
    df = pd.read_sql(query, conn, params=[date])
    
    # Parquet 파일로 저장 (MinIO/S3)
    output_path = f"s3://data-lake/learning-records/{date}.parquet"
    df.to_parquet(output_path, compression='snappy')
    
    return output_path
```

### 4. 객체 스토리지 (MinIO/S3)

대용량 미디어 파일 및 백업 데이터 저장

**저장 데이터**:
- 이미지 (문제 이미지, 프로필 사진)
- 비디오 (강의 영상, 해설 영상)
- 오디오 (발음 파일, 음성 녹음)
- 문서 (PDF 교재, 과제 파일)

---

## 배포 및 운영

### 1. 컨테이너화 (Docker)

각 서비스는 Docker 컨테이너로 패키징되어 배포됩니다.

**Dockerfile 예시**:
```dockerfile
# AI 튜터 서비스 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 거버넌스 통합
ENV OPA_SERVER_URL=http://opa-policy-engine.governance.svc.cluster.local:8181
ENV AUDIT_LOG_LEVEL=INFO

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 서비스 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**이점**:
- 일관된 실행 환경 (Dev/Staging/Prod 동일)
- 격리된 환경 (의존성 충돌 방지)
- 빠른 배포 및 롤백

### 2. 오케스트레이션 (Kubernetes)

Kubernetes를 사용하여 서비스를 배포, 관리, 및 확장합니다.

**Kubernetes Deployment 예시**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-tutor-service
  namespace: dreamseed
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-tutor
  template:
    metadata:
      labels:
        app: ai-tutor
    spec:
      containers:
      - name: ai-tutor
        image: dreamseedai/ai-tutor:v1.2.3
        ports:
        - containerPort: 8000
        env:
        - name: OPA_SERVER_URL
          value: "http://opa-policy-engine.governance.svc.cluster.local:8181"
        - name: AUDIT_LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**자동 스케일링 (HPA)**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-tutor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-tutor-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**고가용성 (Multi-AZ)**:
- 다중 가용 영역 (Availability Zone) 배포
- Pod Anti-Affinity 설정으로 노드 분산
- 자동 복구 (Self-Healing)

---

## 거버넌스 통합

마이크로서비스 아키텍처에서 거버넌스 계층은 모든 서비스에 일관된 정책을 적용합니다.

### 통합 패턴

```
┌─────────────────────────────────────┐
│      API Gateway (Kong/Nginx)        │
│  - 글로벌 정책 적용                   │
│  - PolicyEnforcementMiddleware       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      마이크로서비스 (각각)             │
│  - @require_policy 데코레이터        │
│  - 서비스별 세부 정책                 │
│  - 자동 감사 로깅                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    OPA Policy Engine (중앙)          │
│  - 정책 평가                         │
│  - 결과 반환 (allow/deny)            │
└─────────────────────────────────────┘
```

**상세 예시**: [거버넌스 통합 예시](../governance-integration/examples.md)

---

## 아키텍처 다이어그램

### 전체 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    클라이언트 계층                         │
│           (Web App, Mobile App, Admin Dashboard)         │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                  API Gateway + 거버넌스                    │
│  - 인증/인가 (JWT)                                        │
│  - PolicyEnforcementMiddleware                           │
│  - Rate Limiting                                         │
│  - Logging & Monitoring                                  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                  마이크로서비스 계층                        │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   사용자    │  │   학급     │  │  콘텐츠     │        │
│  │   관리     │  │   관리     │  │   관리     │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  AI 튜터   │  │  평가 엔진  │  │   과제     │        │
│  │           │  │           │  │   배정     │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  ┌────────────┐  ┌────────────┐                        │
│  │ 데이터 분석 │  │   알림     │                        │
│  │           │  │   서비스    │                        │
│  └────────────┘  └────────────┘                        │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                    데이터 계층                            │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ PostgreSQL │  │   Redis    │  │ MinIO/S3   │        │
│  │  (RDBMS)   │  │  (Cache)   │  │  (Object)  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  ┌────────────┐  ┌────────────┐                        │
│  │   Kafka    │  │  Parquet   │                        │
│  │  (Queue)   │  │ (Analytics) │                        │
│  └────────────┘  └────────────┘                        │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│               모니터링 & 거버넌스 계층                      │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Prometheus │  │  Grafana   │  │    OPA     │        │
│  │ (Metrics)  │  │ (Dashbrd)  │  │  (Policy)  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  ┌────────────┐  ┌────────────┐                        │
│  │    ELK     │  │ Alertmgr   │                        │
│  │  (Logs)    │  │  (Alerts)  │                        │
│  └────────────┘  └────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

---

## 결론

DreamSeedAI의 마이크로서비스 아키텍처는 플랫폼의 **확장성, 유지보수성, 및 안정성**을 향상시키는 데 중요한 역할을 합니다. 각 서비스를 독립적으로 개발하고 배포함으로써, DreamSeedAI는 빠르게 변화하는 교육 환경에 유연하게 대응하고, 사용자에게 최상의 학습 경험을 제공할 수 있습니다.

**거버넌스 계층과의 통합**을 통해 모든 마이크로서비스가 일관된 정책을 준수하며, 감사 로깅과 메트릭 수집을 통해 시스템 전체의 안전성과 투명성을 보장합니다.

---

## 참조 문서

- **시스템 계층 홈**: [../README.md](../README.md)
- **거버넌스 통합 예시**: [../governance-integration/examples.md](../governance-integration/examples.md)
- **거버넌스 계층**: [../../../governance/backend/README.md](../../../governance/backend/README.md)
- **Kubernetes 배포**: [../../../governance/ops/k8s/](../../../governance/ops/k8s/)
