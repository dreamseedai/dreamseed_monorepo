# DreamSeedAI: 시스템 계층 (System Layer)

시스템 계층은 DreamSeedAI의 핵심 기술 시스템과 백엔드 인프라를 의미합니다. 여기에는 모든 마이크로서비스, 데이터베이스, AI 모델, 통합 API 등이 포함되며, 실제 기능적 동작을 수행하는 부분입니다. 시스템 계층은 거버넌스/정책 계층의 지침을 준수하면서, 플랫폼이 요구하는 다양한 서비스를 제공합니다.

## 계층 구조

```
┌─────────────────────────────────────────┐
│  정책/거버넌스 계층 (Governance Layer)    │
│  - OPA 정책 엔진                         │
│  - FastAPI 통합 (decorators/middleware)  │
│  - 감사 로깅 & 메트릭                    │
│  📄 governance/backend/README.md         │
└─────────────────────────────────────────┘
              ↓ (정책 적용)
┌─────────────────────────────────────────┐
│  시스템 계층 (System Layer) ← 현재 위치   │
│  - 마이크로서비스 (8개)                  │
│  - AI 모델 (4개 유형)                    │
│  - 데이터베이스 (PostgreSQL/Redis/MinIO) │
│  - API Gateway                          │
│  📂 docs/system_layer/                  │
└─────────────────────────────────────────┘
              ↓ (서비스 제공)
┌─────────────────────────────────────────┐
│  프론트엔드 계층 (Frontend Layer)         │
│  - React/Next.js 애플리케이션            │
│  - 사용자 인터페이스                     │
└─────────────────────────────────────────┘
```

## 📚 문서 구조

### 아키텍처 (Architecture)
- [전체 아키텍처 개요](architecture/overview.md) - 시스템 전체 구조 및 설계 원칙
- 마이크로서비스 아키텍처 (작성 예정)
- 데이터 흐름도 (작성 예정)

### 마이크로서비스 (Services)
- [사용자 관리 서비스](services/user-management.md) - 인증, 권한, 세션 관리
- [학급 관리 서비스](services/class-management.md) - 학급 생성, 학생 관리
- [콘텐츠 관리 서비스](services/content-management.md) - 문항, 학습 자료 관리
- [AI 튜터링 서비스](services/ai-tutoring.md) ⭐ - 질의응답, 맞춤형 학습 (거버넌스 통합)
- [평가 엔진 서비스](services/assessment-engine.md) - 시험 생성, 채점, IRT
- [과제 배정 서비스](services/assignment.md) - 과제 배정 및 관리
- [데이터 분석 서비스](services/data-analytics.md) - 학습 데이터 분석, 리포트
- [알림 서비스](services/notification.md) - 이메일, SMS, 푸시 알림

### 데이터베이스 (Database)
- [PostgreSQL](database/postgresql.md) - 스키마 설계, 인덱스, 파티셔닝
- [Redis](database/redis.md) - 캐싱 전략, 세션 관리
- [MinIO](database/minio.md) - 객체 스토리지, 버킷 구조

### AI 모델 (AI Models)
- [IRT 모델](ai-models/irt-model.md) - 문항 반응 이론, 능력 추정
- [NLP 모델](ai-models/nlp-models.md) - 자연어 처리, 튜터링
- [추천 시스템](ai-models/recommendation.md) - 사용자/콘텐츠 기반 추천
- [이상 감지](ai-models/anomaly-detection.md) - 부정행위 탐지

### API
- [RESTful API](api/rest-api.md) - 엔드포인트 설계, 규칙
- [GraphQL API](api/graphql-api.md) - 스키마, 리졸버
- [API Gateway](api/api-gateway.md) - 인증, 트래픽 관리, 정책 통합

### 🔐 거버넌스 통합 (Governance Integration)
- [정책 적용 가이드](governance-integration/policy-enforcement.md) - 데코레이터, 미들웨어, 수동 방식
- [감사 로깅 통합](governance-integration/audit-logging.md) - 자동 로깅, 커스텀 이벤트
- **[통합 예시 모음](governance-integration/examples.md)** ⭐ - 실제 코드 예시 (AI 튜터, 과제 배정, 데이터 접근)

### 배포 (Deployment)
- [Kubernetes 배포](deployment/kubernetes.md) - 매니페스트, 설정
- [CI/CD 파이프라인](deployment/ci-cd.md) - GitHub Actions, 자동화
- [모니터링 설정](deployment/monitoring.md) - Prometheus, Grafana

## 빠른 시작

### 거버넌스와 함께 사용하기

모든 API 엔드포인트는 거버넌스 계층의 정책을 준수해야 합니다:

```python
from fastapi import FastAPI, Request
from governance.backend import require_policy

app = FastAPI()

@app.post("/api/lessons")
@require_policy("dreamseedai.content.create")  # 정책 자동 적용
async def create_lesson(request: Request, lesson_data: dict):
    # 정책 검증 통과 후 실행됨
    return await lesson_service.create(lesson_data)
```

**상세 예시**: [거버넌스 통합 예시](governance-integration/examples.md)

**상세 예시**: [거버넌스 통합 예시](governance-integration/examples.md)

## 주요 목표

- **기능 제공**: 플랫폼의 핵심 기능을 안정적이고 효율적으로 제공
- **확장성**: 사용자 증가 및 새로운 기능 추가에 유연하게 대응
- **보안**: 데이터 및 시스템 무단 접근 방지, 취약점 최소화
- **유지보수성**: 코드 가독성, 모듈화를 통한 유지보수 용이성
- **정책 준수**: 거버넌스 계층의 규칙 및 제약 조건 준수

## 핵심 구성 요소 개요

### 마이크로서비스 (8개)
1. **사용자 관리**: 인증, 권한, 세션
2. **학급 관리**: 학급, 학생, 과목
3. **콘텐츠 관리**: 문항, 학습 자료
4. **AI 튜터링**: 질의응답, 맞춤형 학습 ⭐
5. **평가 엔진**: 시험, 채점, IRT
6. **과제 배정**: 과제 관리, 제출
7. **데이터 분석**: 학습 데이터, 리포트
8. **알림**: 이메일, SMS, 푸시

### 데이터베이스
- **PostgreSQL**: 정형 데이터 (사용자, 학습 기록, 메타데이터)
- **Redis**: 캐싱, 세션 관리
- **MinIO/S3**: 대용량 객체 (이미지, 비디오, 오디오)

### AI 모델
- **IRT 모델**: 능력 추정, 난이도 분석
- **NLP 모델**: 튜터링, 콘텐츠 분석
- **추천 시스템**: 사용자/콘텐츠 기반
- **이상 감지**: 부정행위, 패턴 이상

### API
- **RESTful API**: 표준 HTTP 기반
- **GraphQL API**: 유연한 쿼리
- **API Gateway**: 인증, 트래픽 관리, 정책 통합 ⭐

## 주요 기술 스택

| 카테고리 | 기술 |
|---------|------|
| **언어** | Python, JavaScript/TypeScript, R |
| **백엔드** | FastAPI, Django |
| **프론트엔드** | React, Next.js |
| **데이터베이스** | PostgreSQL, Redis, MinIO |
| **메시지 큐** | Kafka, Celery |
| **AI/ML** | TensorFlow, PyTorch, scikit-learn |
| **컨테이너** | Docker, Kubernetes |
| **CI/CD** | GitHub Actions, Jenkins |
| **모니터링** | Prometheus, Grafana, ELK |

## 설계 원칙

### 확장성 (Scalability)
- 마이크로서비스 아키텍처로 독립적 확장
- 수평적 확장 (Horizontal Scaling)
- 로드 밸런싱

### 안정성 (Reliability)
- 장애 감지 및 자동 복구
- 서킷 브레이커 패턴
- 헬스 체크

### 보안 (Security)
- API Gateway 중앙 집중식 인증/인가
- 데이터 암호화 (전송/저장)
- **거버넌스 통합**: OPA 정책 엔진 연동 ⭐

### 모니터링 (Monitoring)
- 실시간 메트릭 수집
- 로그 집계 및 분석
- **거버넌스 통합**: 정책 위반 추적 ⭐

## 참조 문서

### 내부 문서
- **거버넌스 계층**: [governance/backend/README.md](../../governance/backend/README.md)
- **OPA 정책**: [governance/policies/](../../governance/policies/)
- **K8s 배포**: [governance/ops/k8s/](../../governance/ops/k8s/)

### 외부 문서
- FastAPI: https://fastapi.tiangolo.com/
- Kubernetes: https://kubernetes.io/docs/
- Prometheus: https://prometheus.io/docs/

---

**다음 단계**: 각 서비스의 상세 설계 문서를 참조하거나, [거버넌스 통합 예시](governance-integration/examples.md)부터 시작하세요.
