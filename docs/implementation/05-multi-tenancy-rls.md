# 05. Multi-Tenancy & Row-Level Security

> **Secure multi-tenant architecture with PostgreSQL Row-Level Security (RLS) for FERPA-compliant data isolation**

## Table of Contents

- [Overview](#overview)
- [Multi-Tenancy Patterns](#multi-tenancy-patterns)
- [PostgreSQL RLS Implementation](#postgresql-rls-implementation)
- [Database Schema Design](#database-schema-design)
- [Application Integration](#application-integration)
- [Performance Optimization](#performance-optimization)
- [Backup & Recovery](#backup--recovery)
- [Testing & Validation](#testing--validation)

---

## Overview

This guide implements **database-enforced multi-tenancy** with:

- **Row-Level Security (RLS)**: PostgreSQL policies for automatic data isolation
- **Organization-based Tenancy**: Each school/organization is a tenant
- **FERPA Compliance**: Legal requirement for US schools
- **Performance**: Optimized for 100+ organizations
- **Security**: Cannot bypass isolation (even with application bugs)

### Why RLS?

| Approach                  | Pros                                             | Cons                                 |
| ------------------------- | ------------------------------------------------ | ------------------------------------ |
| **Application filtering** | Simple                                           | Vulnerable to bugs, not truly secure |
| **Schema per tenant**     | Complete isolation                               | Expensive, migration hell            |
| **Database per tenant**   | Maximum isolation                                | Very expensive, hard to maintain     |
| **RLS (our choice)**      | ✅ Secure, ✅ Cost-effective, ✅ Easy migrations | Requires PostgreSQL 9.5+             |

---

## Multi-Tenancy Patterns

### Tenant Hierarchy

```
Organization (Tenant)
├── Users (admins, teachers, students)
├── Classes
├── Content (items, assessments)
├── Learning Data (responses, scores)
└── Subscriptions (payments, licenses)
```

### Tenant Identification

```python
# Every request includes organization_id in JWT token
{
  "sub": "user-uuid",
  "org_id": "org-uuid",  # ← Tenant identifier
  "role": "teacher"
}
```

---

## PostgreSQL RLS Implementation

### Step 1: Enable RLS Extension

```sql
-- Enable RLS (one-time setup)
ALTER DATABASE dreamseed SET row_security = on;
```

### Step 2: Create Base Schema

```sql
-- Organizations table (tenant registry)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(50) NOT NULL, -- 'individual', 'school', 'enterprise'
    max_seats INT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_active ON organizations(is_active);
```

### Step 3: Create Multi-Tenant Tables with RLS

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL, -- 'admin', 'teacher', 'student'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, email)
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see their organization's data
CREATE POLICY users_org_isolation ON users
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Indexes for performance
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(organization_id, role);
```

### Step 4: Apply RLS to All Tenant Tables

```sql
-- Items table
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    difficulty NUMERIC(5,3),
    discrimination NUMERIC(5,3) DEFAULT 1.0,
    guessing NUMERIC(5,3) DEFAULT 0.0,
    content_area VARCHAR(100),
    skill_tags TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE items ENABLE ROW LEVEL SECURITY;

CREATE POLICY items_org_isolation ON items
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

CREATE INDEX idx_items_org ON items(organization_id);
CREATE INDEX idx_items_content_area ON items(organization_id, content_area);
CREATE INDEX idx_items_active ON items(organization_id, is_active);


-- Assessments table
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id),
    model_type VARCHAR(10) NOT NULL,
    ability_estimate NUMERIC(5,3),
    standard_error NUMERIC(5,3),
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY assessments_org_isolation ON assessments
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

CREATE INDEX idx_assessments_org ON assessments(organization_id);
CREATE INDEX idx_assessments_student ON assessments(organization_id, student_id);
CREATE INDEX idx_assessments_status ON assessments(organization_id, status);


-- Responses table
CREATE TABLE responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id),
    response_value TEXT,
    is_correct BOOLEAN,
    response_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY responses_org_isolation ON responses
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

CREATE INDEX idx_responses_org ON responses(organization_id);
CREATE INDEX idx_responses_assessment ON responses(assessment_id);
```

### Step 5: Admin Bypass Policy (Optional)

```sql
-- Super admin role can see all data (for platform administration)
CREATE POLICY admin_bypass ON users
    FOR ALL
    TO admin_role
    USING (true);  -- No restriction

-- Create admin role
CREATE ROLE admin_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin_role;
```

---

## Database Schema Design

### Partitioning for Scale

For high-volume tables (millions of rows), use **partitioning**:

```sql
-- Partition assessments by organization (hash partitioning)
CREATE TABLE assessments (
    id UUID NOT NULL,
    organization_id UUID NOT NULL,
    student_id UUID NOT NULL,
    -- ... other columns
    PRIMARY KEY (id, organization_id)
) PARTITION BY HASH (organization_id);

-- Create 8 partitions
CREATE TABLE assessments_p0 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE assessments_p1 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE assessments_p2 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE assessments_p3 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE assessments_p4 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE assessments_p5 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE assessments_p6 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE assessments_p7 PARTITION OF assessments FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- RLS still applies to partitioned tables
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY assessments_org_isolation ON assessments
    FOR ALL
    USING (organization_id = current_setting('app.current_organization_id')::uuid);
```

### Migration Script (Alembic)

```python
# alembic/versions/001_add_rls_policies.py
from alembic import op
import sqlalchemy as sa


def upgrade():
    """Enable RLS on all tenant tables"""

    # Enable RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE items ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE responses ENABLE ROW LEVEL SECURITY;")

    # Create policies
    op.execute("""
        CREATE POLICY users_org_isolation ON users
        FOR ALL
        USING (organization_id = current_setting('app.current_organization_id')::uuid);
    """)

    op.execute("""
        CREATE POLICY items_org_isolation ON items
        FOR ALL
        USING (organization_id = current_setting('app.current_organization_id')::uuid);
    """)

    op.execute("""
        CREATE POLICY assessments_org_isolation ON assessments
        FOR ALL
        USING (organization_id = current_setting('app.current_organization_id')::uuid);
    """)

    op.execute("""
        CREATE POLICY responses_org_isolation ON responses
        FOR ALL
        USING (organization_id = current_setting('app.current_organization_id')::uuid);
    """)


def downgrade():
    """Disable RLS"""

    # Drop policies
    op.execute("DROP POLICY IF EXISTS users_org_isolation ON users;")
    op.execute("DROP POLICY IF EXISTS items_org_isolation ON items;")
    op.execute("DROP POLICY IF EXISTS assessments_org_isolation ON assessments;")
    op.execute("DROP POLICY IF EXISTS responses_org_isolation ON responses;")

    # Disable RLS
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE items DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE assessments DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE responses DISABLE ROW LEVEL SECURITY;")
```

---

## Application Integration

### FastAPI Middleware (Set Organization Context)

```python
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.utils.auth import decode_jwt


async def set_organization_context(request: Request, call_next):
    """
    Middleware to set PostgreSQL session variable for RLS

    Extracts organization_id from JWT and sets it in database session
    """
    # Skip for health checks
    if request.url.path in ["/health", "/ready", "/metrics"]:
        return await call_next(request)

    # Extract JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")

    token = auth_header.split(" ")[1]

    try:
        # Decode JWT
        payload = decode_jwt(token)
        organization_id = payload.get("org_id")

        if not organization_id:
            raise HTTPException(status_code=401, detail="Missing organization_id in token")

        # Set organization context in request state
        request.state.organization_id = organization_id

        # Set PostgreSQL session variable for RLS
        db: Session = next(get_db())
        db.execute(f"SET LOCAL app.current_organization_id = '{organization_id}'")
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    response = await call_next(request)
    return response


# Add to FastAPI app
from fastapi import FastAPI

app = FastAPI()
app.middleware("http")(set_organization_context)
```

### SQLAlchemy Session with RLS

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

def set_organization_id(session: Session, organization_id: str):
    """Set organization context for RLS in SQLAlchemy session"""
    session.execute(f"SET LOCAL app.current_organization_id = '{organization_id}'")


# Usage in dependency
def get_db_with_org(organization_id: str):
    """Database session with organization context set"""
    db = SessionLocal()
    try:
        set_organization_id(db, organization_id)
        yield db
    finally:
        db.close()
```

### Repository Pattern with RLS

```python
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.user import User


class UserRepository:
    """User repository - RLS automatically filters by organization"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[User]:
        """
        Get all users

        Note: RLS automatically filters to current organization
        No need to add WHERE organization_id = ...
        """
        return self.db.query(User).all()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (within current organization)"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_role(self, role: str) -> List[User]:
        """Get users by role (within current organization)"""
        return self.db.query(User).filter(User.role == role).all()

    def create(self, user: User) -> User:
        """
        Create user

        Note: Must set organization_id before insert
        """
        # organization_id should already be set by caller
        if not user.organization_id:
            raise ValueError("organization_id is required")

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
```

---

## Performance Optimization

### Indexing Strategy

```sql
-- CRITICAL: organization_id must be first column in composite indexes
-- This allows PostgreSQL to use indexes efficiently with RLS

-- Good (org_id first)
CREATE INDEX idx_users_org_role ON users(organization_id, role);

-- Bad (org_id not first) - slower with RLS
CREATE INDEX idx_users_role_org ON users(role, organization_id);


-- For foreign key lookups
CREATE INDEX idx_responses_assessment ON responses(organization_id, assessment_id);

-- For common queries
CREATE INDEX idx_assessments_student_status
    ON assessments(organization_id, student_id, status);
```

### Query Performance Testing

```python
import time
from sqlalchemy import text

def test_rls_performance(db: Session, organization_id: str):
    """Test RLS query performance"""

    # Set organization context
    db.execute(f"SET LOCAL app.current_organization_id = '{organization_id}'")

    # Test query with EXPLAIN ANALYZE
    query = """
        EXPLAIN ANALYZE
        SELECT * FROM users
        WHERE role = 'student';
    """

    start = time.time()
    result = db.execute(text(query))
    duration = time.time() - start

    print(f"Query took {duration:.3f}s")
    print("\n".join([row[0] for row in result]))

    # Should see "Index Scan" on idx_users_org_role
    # RLS adds: organization_id = current_setting(...)
```

### Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Base pool size
    max_overflow=40,           # Max connections
    pool_pre_ping=True,        # Verify connections
    pool_recycle=3600,         # Recycle after 1 hour
    echo_pool=False
)

# Each connection maintains its own session variables
# So organization context is isolated per connection
```

---

## Backup & Recovery

### Per-Tenant Backup

```bash
#!/bin/bash
# backup_tenant.sh - Backup single organization's data

ORG_ID=$1
BACKUP_FILE="backup_${ORG_ID}_$(date +%Y%m%d_%H%M%S).sql"

# Set organization context and dump
psql -d dreamseed -c "SET app.current_organization_id = '$ORG_ID';" \
  | pg_dump -d dreamseed \
    --table=users \
    --table=items \
    --table=assessments \
    --table=responses \
    --file=$BACKUP_FILE

echo "Backup saved to $BACKUP_FILE"
```

### Restore Tenant Data

```bash
#!/bin/bash
# restore_tenant.sh - Restore organization's data

BACKUP_FILE=$1
ORG_ID=$2

# Restore to temporary schema
psql -d dreamseed -c "CREATE SCHEMA IF NOT EXISTS temp_restore;"
psql -d dreamseed -f $BACKUP_FILE --schema=temp_restore

# Copy data to production (RLS will enforce organization_id)
psql -d dreamseed <<EOF
SET app.current_organization_id = '$ORG_ID';

INSERT INTO users SELECT * FROM temp_restore.users;
INSERT INTO items SELECT * FROM temp_restore.items;
INSERT INTO assessments SELECT * FROM temp_restore.assessments;
INSERT INTO responses SELECT * FROM temp_restore.responses;

DROP SCHEMA temp_restore CASCADE;
EOF

echo "Restored data for organization $ORG_ID"
```

---

## Testing & Validation

### RLS Security Test

```python
import pytest
from uuid import uuid4

def test_rls_isolation(db):
    """Test that RLS prevents cross-tenant access"""

    # Create two organizations
    org1_id = uuid4()
    org2_id = uuid4()

    org1 = Organization(id=org1_id, name="Org 1", slug="org1")
    org2 = Organization(id=org2_id, name="Org 2", slug="org2")
    db.add(org1)
    db.add(org2)
    db.commit()

    # Create users in each org
    user1 = User(organization_id=org1_id, email="user1@org1.com", role="student")
    user2 = User(organization_id=org2_id, email="user2@org2.com", role="student")
    db.add(user1)
    db.add(user2)
    db.commit()

    # Set context to org1
    db.execute(f"SET LOCAL app.current_organization_id = '{org1_id}'")

    # Query should only return org1's user
    users = db.query(User).all()
    assert len(users) == 1
    assert users[0].email == "user1@org1.com"

    # Switch to org2
    db.execute(f"SET LOCAL app.current_organization_id = '{org2_id}'")

    # Query should only return org2's user
    users = db.query(User).all()
    assert len(users) == 1
    assert users[0].email == "user2@org2.com"

    print("✅ RLS isolation working correctly")


def test_rls_insert_protection(db):
    """Test that RLS prevents inserting into wrong organization"""

    org1_id = uuid4()
    org2_id = uuid4()

    org1 = Organization(id=org1_id, name="Org 1", slug="org1")
    org2 = Organization(id=org2_id, name="Org 2", slug="org2")
    db.add_all([org1, org2])
    db.commit()

    # Set context to org1
    db.execute(f"SET LOCAL app.current_organization_id = '{org1_id}'")

    # Try to insert user for org2 (should be blocked or isolated)
    user = User(organization_id=org2_id, email="user@org2.com", role="student")
    db.add(user)

    with pytest.raises(Exception):
        db.commit()  # Should fail due to RLS

    db.rollback()
    print("✅ RLS insert protection working")


def test_performance_with_many_orgs(db):
    """Test RLS performance with many organizations"""
    import time

    # Create 100 organizations
    orgs = [
        Organization(id=uuid4(), name=f"Org {i}", slug=f"org{i}")
        for i in range(100)
    ]
    db.add_all(orgs)
    db.commit()

    # Create 100 users per org (10,000 total)
    for org in orgs:
        users = [
            User(organization_id=org.id, email=f"user{j}@{org.slug}.com", role="student")
            for j in range(100)
        ]
        db.add_all(users)
    db.commit()

    # Test query performance for one org
    test_org = orgs[50]
    db.execute(f"SET LOCAL app.current_organization_id = '{test_org.id}'")

    start = time.time()
    users = db.query(User).filter(User.role == "student").all()
    duration = time.time() - start

    assert len(users) == 100  # Should only return test_org's users
    assert duration < 0.1  # Should be fast (<100ms)

    print(f"✅ Query with RLS took {duration*1000:.2f}ms for 10,000 total users")
```

---

## Cross-Tenant Analytics (Special Case)

Sometimes you need **aggregated data across organizations** (e.g., benchmarking):

### Anonymous Aggregation

```sql
-- Create view for cross-tenant analytics (no RLS)
CREATE VIEW anonymous_benchmarks AS
SELECT
    content_area,
    AVG(ability_estimate) AS avg_ability,
    STDDEV(ability_estimate) AS std_ability,
    COUNT(*) AS num_students
FROM assessments
WHERE status = 'completed'
GROUP BY content_area;

-- Grant access to analytics role
GRANT SELECT ON anonymous_benchmarks TO analytics_role;
```

### Secure Reporting Function

```python
def get_benchmark_data(db: Session, content_area: str) -> dict:
    """
    Get anonymous benchmark data (bypasses RLS)

    Note: Returns only aggregated data, no individual records
    """
    # Use separate connection without RLS for analytics
    analytics_engine = create_engine(
        DATABASE_URL,
        connect_args={"options": "-c session_preload_libraries=''"}
    )

    with analytics_engine.connect() as conn:
        result = conn.execute(f"""
            SELECT avg_ability, std_ability, num_students
            FROM anonymous_benchmarks
            WHERE content_area = '{content_area}'
        """).fetchone()

    return {
        "content_area": content_area,
        "avg_ability": float(result[0]),
        "std_ability": float(result[1]),
        "num_students": int(result[2])
    }
```

---

## Next Steps

1. ✅ **Apply Migrations**: Run `alembic upgrade head` to enable RLS
2. 🔧 **Test Isolation**: Run security tests to verify RLS
3. 📊 **Monitor Performance**: Check query plans with EXPLAIN ANALYZE
4. 🔐 **Audit Logs**: Combine with Kafka for immutable audit trail
5. 📖 **Document**: Update team docs with RLS patterns

**Related Guides**:

- [00-architecture-overview.md](./00-architecture-overview.md) - ADR on RLS decision
- [01-fastapi-microservices.md](./01-fastapi-microservices.md) - Middleware integration
- [10-security-compliance.md](./10-security-compliance.md) - FERPA compliance

---

_Last Updated: November 9, 2025_
_Version: 1.0.0_
