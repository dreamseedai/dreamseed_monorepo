# 01. FastAPI Microservices Best Practices

> **Production-ready patterns for building DreamSeedAI microservices with FastAPI, including project structure, dependency injection, testing, and deployment**

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Service Implementation](#service-implementation)
- [Database Integration](#database-integration)
- [Authentication & Authorization](#authentication--authorization)
- [Error Handling](#error-handling)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)

---

## Overview

This guide covers building production-ready FastAPI microservices with:
- **Clean Architecture**: Domain-driven design with clear layers
- **Dependency Injection**: Using FastAPI's DI system
- **Type Safety**: Pydantic models for validation
- **Testing**: Comprehensive test coverage
- **Observability**: Metrics, logs, traces
- **Security**: Multi-tenancy, RBAC, input validation

---

## Project Structure

### Recommended Directory Layout

```
services/assessment/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration (Pydantic Settings)
│   ├── dependencies.py         # DI providers
│   │
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # Main v1 router
│   │   │   └── endpoints/
│   │   │       ├── assessments.py
│   │   │       ├── items.py
│   │   │       └── health.py
│   │   └── deps.py             # API dependencies (auth, pagination)
│   │
│   ├── core/                   # Business logic
│   │   ├── __init__.py
│   │   ├── irt/                # IRT engine
│   │   │   ├── models.py       # IRT models (1PL, 2PL, 3PL)
│   │   │   ├── cat.py          # CAT algorithm
│   │   │   └── estimation.py   # Ability estimation
│   │   └── services/
│   │       ├── assessment.py   # Assessment service
│   │       └── item.py         # Item service
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model with common fields
│   │   ├── assessment.py
│   │   └── item.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── assessment.py
│   │   └── item.py
│   │
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py             # Generic repository
│   │   ├── assessment.py
│   │   └── item.py
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── security.py
│       ├── cache.py
│       └── metrics.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   ├── unit/
│   │   ├── test_irt.py
│   │   └── test_services.py
│   ├── integration/
│   │   └── test_api.py
│   └── e2e/
│       └── test_cat_session.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml              # Project metadata
├── .env.example
└── README.md
```

---

## Service Implementation

### 1. Main Application (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging

from app.config import settings
from app.api.v1.router import api_router
from app.utils.metrics import setup_metrics
from app.dependencies import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Assessment Service", extra={
        "service": "assessment",
        "version": settings.VERSION
    })
    
    # Initialize metrics
    setup_metrics(app)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Assessment Service")


# Create FastAPI app
app = FastAPI(
    title="DreamSeed Assessment Service",
    description="IRT-based Computerized Adaptive Testing (CAT) engine",
    version=settings.VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# Request context middleware (for multi-tenancy)
@app.middleware("http")
async def add_organization_context(request: Request, call_next):
    """Set organization context for RLS"""
    # Extract organization from JWT token
    org_id = request.state.organization_id if hasattr(request.state, "organization_id") else None
    
    if org_id:
        # Set PostgreSQL session variable for RLS
        db = next(get_db())
        db.execute(f"SET app.current_organization_id = '{org_id}'")
        db.commit()
    
    response = await call_next(request)
    return response


# Include API routers
app.include_router(api_router, prefix="/api/v1")


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "assessment",
        "version": settings.VERSION
    }


@app.get("/ready")
async def readiness_check(db=Depends(get_db)):
    """Readiness probe (checks DB connection)"""
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")
```

---

### 2. Configuration (`app/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings (from environment variables)"""
    
    # App
    APP_NAME: str = "assessment-service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    # OPA (Policy Engine)
    OPA_URL: str = "http://opa:8181"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

### 3. Database Session (`app/dependencies.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator

from app.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 4. Base Model (`app/models/base.py`)

```python
from sqlalchemy import Column, DateTime, UUID
from sqlalchemy.sql import func
from app.dependencies import Base
import uuid


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

### 5. SQLAlchemy Models (`app/models/assessment.py`)

```python
from sqlalchemy import Column, String, UUID, ForeignKey, Integer, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Assessment(BaseModel):
    """Assessment (test session) model"""
    __tablename__ = "assessments"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # CAT configuration
    model_type = Column(String(10), nullable=False)  # '1PL', '2PL', '3PL'
    max_items = Column(Integer, default=30)
    target_se = Column(Numeric(4, 3), default=0.3)
    
    # Results
    ability_estimate = Column(Numeric(5, 3))
    standard_error = Column(Numeric(5, 3))
    items_administered = Column(Integer, default=0)
    status = Column(String(20), default="in_progress")  # in_progress, completed, abandoned
    
    # Relationships
    student = relationship("User", back_populates="assessments")
    responses = relationship("Response", back_populates="assessment", cascade="all, delete-orphan")


class Response(BaseModel):
    """Student response to an item"""
    __tablename__ = "responses"
    
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    
    response_value = Column(String(255))  # Student's answer
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)    # Time to answer (milliseconds)
    ability_estimate = Column(Numeric(5, 3))  # Ability after this item
    
    # Relationships
    assessment = relationship("Assessment", back_populates="responses")
    item = relationship("Item")
```

---

### 6. Pydantic Schemas (`app/schemas/assessment.py`)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class AssessmentCreate(BaseModel):
    """Schema for creating an assessment"""
    student_id: UUID
    model_type: str = Field(..., pattern="^(1PL|2PL|3PL)$")
    max_items: int = Field(default=30, ge=5, le=100)
    target_se: float = Field(default=0.3, ge=0.1, le=0.5)


class AssessmentResponse(BaseModel):
    """Schema for assessment response"""
    id: UUID
    student_id: UUID
    model_type: str
    ability_estimate: Optional[float]
    standard_error: Optional[float]
    items_administered: int
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ItemResponse(BaseModel):
    """Schema for submitting an item response"""
    item_id: UUID
    response_value: str
    response_time_ms: int = Field(..., ge=0)


class NextItemResponse(BaseModel):
    """Schema for next item recommendation"""
    item_id: UUID
    content: str
    estimated_difficulty: float
    information: float
```

---

### 7. Repository Pattern (`app/repositories/assessment.py`)

```python
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.assessment import Assessment, Response
from app.repositories.base import BaseRepository


class AssessmentRepository(BaseRepository[Assessment]):
    """Repository for Assessment operations"""
    
    def __init__(self, db: Session):
        super().__init__(Assessment, db)
    
    def get_by_student(self, student_id: UUID, status: Optional[str] = None) -> List[Assessment]:
        """Get assessments by student"""
        query = self.db.query(Assessment).filter(Assessment.student_id == student_id)
        if status:
            query = query.filter(Assessment.status == status)
        return query.order_by(Assessment.created_at.desc()).all()
    
    def get_active_assessment(self, student_id: UUID) -> Optional[Assessment]:
        """Get active (in-progress) assessment for student"""
        return self.db.query(Assessment).filter(
            Assessment.student_id == student_id,
            Assessment.status == "in_progress"
        ).first()
    
    def update_ability_estimate(self, assessment_id: UUID, ability: float, se: float) -> Assessment:
        """Update ability estimate and standard error"""
        assessment = self.get(assessment_id)
        assessment.ability_estimate = ability
        assessment.standard_error = se
        assessment.items_administered += 1
        self.db.commit()
        self.db.refresh(assessment)
        return assessment


class ResponseRepository(BaseRepository[Response]):
    """Repository for Response operations"""
    
    def __init__(self, db: Session):
        super().__init__(Response, db)
    
    def get_by_assessment(self, assessment_id: UUID) -> List[Response]:
        """Get all responses for an assessment"""
        return self.db.query(Response).filter(
            Response.assessment_id == assessment_id
        ).order_by(Response.created_at).all()
```

---

### 8. Service Layer (`app/core/services/assessment.py`)

```python
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, Response
from app.repositories.assessment import AssessmentRepository, ResponseRepository
from app.core.irt.cat import CATEngine
from app.core.irt.models import IRTModel
from app.schemas.assessment import AssessmentCreate, ItemResponse


class AssessmentService:
    """Business logic for assessments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.assessment_repo = AssessmentRepository(db)
        self.response_repo = ResponseRepository(db)
        self.cat_engine = CATEngine()
    
    def create_assessment(self, data: AssessmentCreate, organization_id: UUID) -> Assessment:
        """Create new assessment"""
        # Check if student has active assessment
        active = self.assessment_repo.get_active_assessment(data.student_id)
        if active:
            raise ValueError(f"Student {data.student_id} already has an active assessment")
        
        assessment = Assessment(
            organization_id=organization_id,
            student_id=data.student_id,
            model_type=data.model_type,
            max_items=data.max_items,
            target_se=data.target_se,
            status="in_progress"
        )
        return self.assessment_repo.create(assessment)
    
    def get_next_item(self, assessment_id: UUID) -> Tuple[UUID, float]:
        """Get next item using CAT algorithm"""
        assessment = self.assessment_repo.get(assessment_id)
        responses = self.response_repo.get_by_assessment(assessment_id)
        
        # Get current ability estimate
        if not responses:
            # Initial ability estimate (neutral)
            current_ability = 0.0
        else:
            current_ability = assessment.ability_estimate
        
        # Get administered item IDs
        administered_ids = [r.item_id for r in responses]
        
        # Select next item using CAT engine
        next_item_id, information = self.cat_engine.select_next_item(
            current_ability=current_ability,
            administered_items=administered_ids,
            organization_id=assessment.organization_id
        )
        
        return next_item_id, information
    
    def submit_response(
        self,
        assessment_id: UUID,
        data: ItemResponse,
        organization_id: UUID
    ) -> Tuple[float, float, bool]:
        """Submit item response and update ability estimate"""
        assessment = self.assessment_repo.get(assessment_id)
        
        # Score the response
        is_correct = self._score_response(data.item_id, data.response_value)
        
        # Get all responses including this one
        responses = self.response_repo.get_by_assessment(assessment_id)
        response_pattern = [r.is_correct for r in responses] + [is_correct]
        
        # Estimate ability using IRT
        irt_model = IRTModel(model_type=assessment.model_type)
        ability, se = irt_model.estimate_ability(
            responses=response_pattern,
            item_ids=[r.item_id for r in responses] + [data.item_id],
            organization_id=organization_id
        )
        
        # Save response
        response = Response(
            organization_id=organization_id,
            assessment_id=assessment_id,
            item_id=data.item_id,
            response_value=data.response_value,
            is_correct=is_correct,
            response_time_ms=data.response_time_ms,
            ability_estimate=ability
        )
        self.response_repo.create(response)
        
        # Update assessment
        assessment = self.assessment_repo.update_ability_estimate(assessment_id, ability, se)
        
        # Check stopping criteria
        is_finished = self._check_stopping_criteria(assessment)
        if is_finished:
            assessment.status = "completed"
            self.db.commit()
        
        return ability, se, is_finished
    
    def _score_response(self, item_id: UUID, response_value: str) -> bool:
        """Score a response (check if correct)"""
        # TODO: Implement actual scoring logic
        # For now, assume multiple choice with correct_answer stored in item
        from app.repositories.item import ItemRepository
        item_repo = ItemRepository(self.db)
        item = item_repo.get(item_id)
        return response_value == item.correct_answer
    
    def _check_stopping_criteria(self, assessment: Assessment) -> bool:
        """Check if assessment should stop"""
        # Stop if max items reached
        if assessment.items_administered >= assessment.max_items:
            return True
        
        # Stop if standard error below target
        if assessment.standard_error and assessment.standard_error <= assessment.target_se:
            return True
        
        return False
```

---

### 9. API Endpoint (`app/api/v1/endpoints/assessments.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.dependencies import get_db
from app.api.deps import get_current_user, get_organization_id
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    ItemResponse,
    NextItemResponse
)
from app.core.services.assessment import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Create a new assessment"""
    service = AssessmentService(db)
    
    try:
        assessment = service.create_assessment(data, organization_id)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get assessment by ID"""
    service = AssessmentService(db)
    assessment = service.assessment_repo.get(assessment_id)
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return assessment


@router.get("/{assessment_id}/next-item", response_model=NextItemResponse)
def get_next_item(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get next item for assessment (CAT algorithm)"""
    service = AssessmentService(db)
    
    try:
        item_id, information = service.get_next_item(assessment_id)
        
        # Fetch item details
        from app.repositories.item import ItemRepository
        item_repo = ItemRepository(db)
        item = item_repo.get(item_id)
        
        return NextItemResponse(
            item_id=item.id,
            content=item.content,
            estimated_difficulty=item.difficulty,
            information=information
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assessment_id}/responses", response_model=dict)
def submit_response(
    assessment_id: UUID,
    data: ItemResponse,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_id)
):
    """Submit response to an item"""
    service = AssessmentService(db)
    
    try:
        ability, se, is_finished = service.submit_response(assessment_id, data, organization_id)
        
        return {
            "ability_estimate": ability,
            "standard_error": se,
            "is_finished": is_finished,
            "message": "Assessment completed" if is_finished else "Continue to next item"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 10. Authentication Dependency (`app/api/deps.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from uuid import UUID

from app.config import settings

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT token and return user info"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {
            "user_id": UUID(user_id),
            "organization_id": UUID(payload.get("org_id")),
            "role": payload.get("role")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def get_organization_id(current_user: dict = Depends(get_current_user)) -> UUID:
    """Extract organization ID from current user"""
    return current_user["organization_id"]
```

---

## Testing Strategy

### Pytest Configuration (`tests/conftest.py`)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.dependencies import get_db, Base

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create test user"""
    from app.models.user import User
    import uuid
    
    user = User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="test@example.com",
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### Unit Test Example (`tests/unit/test_irt.py`)

```python
import pytest
from app.core.irt.models import IRTModel


def test_1pl_probability():
    """Test 1PL IRT probability calculation"""
    model = IRTModel(model_type="1PL")
    
    # Test at theta = 0, difficulty = 0 (should be 0.5)
    prob = model.probability(theta=0.0, difficulty=0.0)
    assert abs(prob - 0.5) < 0.01
    
    # Test at theta = 1, difficulty = 0 (should be > 0.5)
    prob = model.probability(theta=1.0, difficulty=0.0)
    assert prob > 0.5


def test_ability_estimation():
    """Test MLE ability estimation"""
    model = IRTModel(model_type="2PL")
    
    # Perfect score should give high ability
    responses = [True] * 10
    difficulties = [0.0] * 10
    discriminations = [1.0] * 10
    
    ability, se = model.estimate_ability_mle(responses, difficulties, discriminations)
    assert ability > 2.0
    assert se < 0.5
```

### Integration Test Example (`tests/integration/test_api.py`)

```python
def test_create_assessment(client, test_user):
    """Test creating an assessment via API"""
    response = client.post(
        "/api/v1/assessments/",
        json={
            "student_id": str(test_user.id),
            "model_type": "2PL",
            "max_items": 20,
            "target_se": 0.3
        },
        headers={"Authorization": f"Bearer {generate_test_token(test_user)}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == str(test_user.id)
    assert data["status"] == "in_progress"
```

---

## Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Next Steps

1. ✅ **Understand Structure**: Review this guide
2. 📖 **Implement IRT Engine**: See [02-irt-cat-implementation.md](./02-irt-cat-implementation.md)
3. 🔐 **Add Multi-Tenancy**: See [05-multi-tenancy-rls.md](./05-multi-tenancy-rls.md)
4. 🧪 **Write Tests**: Follow testing examples above

---

*Last Updated: November 9, 2025*
