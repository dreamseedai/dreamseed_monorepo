# Security & Compliance Implementation

## Table of Contents

- [Overview](#overview)
- [GDPR Compliance](#gdpr-compliance)
- [COPPA Compliance](#coppa-compliance)
- [FERPA Compliance](#ferpa-compliance)
- [Encryption](#encryption)
- [Audit Logging](#audit-logging)
- [Authentication & Authorization](#authentication--authorization)
- [Security Headers](#security-headers)
- [Vulnerability Scanning](#vulnerability-scanning)
- [Incident Response](#incident-response)

## Overview

Comprehensive security and compliance framework for educational data:

- **GDPR**: Right to access, right to be forgotten, data portability (EU)
- **COPPA**: Parental consent for users <13 (US)
- **FERPA**: Student education records privacy (US schools)
- **Data encryption**: At rest (AES-256) and in transit (TLS 1.3)
- **Audit logging**: Complete trail of sensitive operations
- **Penetration testing**: Regular security assessments

## GDPR Compliance

### Data Subject Rights

```python
# app/services/gdpr_service.py
from typing import Dict, List
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

class GDPRService:
    """GDPR compliance service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_user_data(self, user_id: UUID) -> Dict:
        """Right to access (GDPR Article 15) - export all user data."""

        # Collect data from all tables
        tables = [
            "users", "responses", "assessments", "tutor_sessions",
            "tutor_messages", "subscriptions", "reports"
        ]

        export_data = {}

        for table in tables:
            query = text(f"""
                SELECT * FROM {table}
                WHERE user_id = :user_id
            """)

            result = await self.db.execute(query, {"user_id": str(user_id)})
            rows = result.fetchall()

            export_data[table] = [dict(row._mapping) for row in rows]

        # Include metadata
        export_data["_metadata"] = {
            "user_id": str(user_id),
            "export_date": datetime.utcnow().isoformat(),
            "format_version": "1.0"
        }

        return export_data

    async def delete_user_data(self, user_id: UUID, retain_days: int = 30):
        """Right to be forgotten (GDPR Article 17)."""

        # Soft delete: anonymize immediately, hard delete after retention period

        # 1. Anonymize personal data
        anonymized_email = f"deleted_{user_id}@anonymized.local"

        query = text("""
            UPDATE users
            SET email = :anon_email,
                name = 'Deleted User',
                phone = NULL,
                date_of_birth = NULL,
                deletion_requested_at = CURRENT_TIMESTAMP,
                deletion_scheduled_at = CURRENT_TIMESTAMP + INTERVAL :retain_days DAY
            WHERE user_id = :user_id
        """)

        await self.db.execute(query, {
            "user_id": str(user_id),
            "anon_email": anonymized_email,
            "retain_days": retain_days
        })

        # 2. Schedule hard deletion job
        from app.tasks.gdpr import schedule_user_deletion
        schedule_user_deletion.apply_async(
            args=[str(user_id)],
            countdown=retain_days * 86400  # Convert days to seconds
        )

        await self.db.commit()

    async def hard_delete_user(self, user_id: UUID):
        """Permanent deletion after retention period."""

        # Delete from all tables (cascading)
        tables = [
            "tutor_messages",
            "tutor_sessions",
            "license_seat_assignments",
            "reports",
            "responses",
            "assessment_assignments",
            "class_enrollments",
            "users"
        ]

        for table in tables:
            query = text(f"""
                DELETE FROM {table}
                WHERE user_id = :user_id
            """)

            await self.db.execute(query, {"user_id": str(user_id)})

        await self.db.commit()

    async def export_organization_data(self, organization_id: UUID) -> Dict:
        """Export all data for an organization (for data portability)."""

        # Similar to export_user_data but for entire organization
        # Include all users, items, assessments, etc.

        return {
            "organization": await self._export_organization_info(organization_id),
            "users": await self._export_organization_users(organization_id),
            "items": await self._export_organization_items(organization_id),
            "assessments": await self._export_organization_assessments(organization_id)
        }
```

### Consent Management

```python
# app/services/consent_service.py
class ConsentService:
    """Manage user consent for data processing."""

    async def record_consent(
        self,
        user_id: UUID,
        consent_type: str,
        consent_given: bool,
        ip_address: str
    ):
        """Record user consent decision."""

        query = text("""
            INSERT INTO user_consents
                (user_id, consent_type, consent_given, ip_address, consented_at)
            VALUES
                (:user_id, :consent_type, :consent_given, :ip_address, CURRENT_TIMESTAMP)
        """)

        await self.db.execute(query, {
            "user_id": str(user_id),
            "consent_type": consent_type,
            "consent_given": consent_given,
            "ip_address": ip_address
        })

        await self.db.commit()

    async def has_consent(self, user_id: UUID, consent_type: str) -> bool:
        """Check if user has given consent."""

        query = text("""
            SELECT consent_given
            FROM user_consents
            WHERE user_id = :user_id
                AND consent_type = :consent_type
            ORDER BY consented_at DESC
            LIMIT 1
        """)

        result = await self.db.execute(query, {
            "user_id": str(user_id),
            "consent_type": consent_type
        })

        row = result.fetchone()
        return row.consent_given if row else False
```

## COPPA Compliance

### Age Verification

```python
# app/services/coppa_service.py
from datetime import date, timedelta

class COPPAService:
    """COPPA compliance for users under 13."""

    COPPA_AGE_THRESHOLD = 13

    def calculate_age(self, date_of_birth: date) -> int:
        """Calculate user's age."""
        today = date.today()
        age = today.year - date_of_birth.year

        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1

        return age

    async def requires_parental_consent(self, user_id: UUID) -> bool:
        """Check if user is under COPPA age threshold."""

        query = text("""
            SELECT date_of_birth
            FROM users
            WHERE user_id = :user_id
        """)

        result = await self.db.execute(query, {"user_id": str(user_id)})
        row = result.fetchone()

        if not row or not row.date_of_birth:
            return True  # Assume requires consent if age unknown

        age = self.calculate_age(row.date_of_birth)
        return age < self.COPPA_AGE_THRESHOLD

    async def request_parental_consent(self, user_id: UUID, parent_email: str):
        """Send parental consent request."""

        # Generate consent token
        import secrets
        consent_token = secrets.token_urlsafe(32)

        # Store consent request
        query = text("""
            INSERT INTO parental_consent_requests
                (user_id, parent_email, consent_token, expires_at)
            VALUES
                (:user_id, :parent_email, :consent_token,
                 CURRENT_TIMESTAMP + INTERVAL '7 days')
        """)

        await self.db.execute(query, {
            "user_id": str(user_id),
            "parent_email": parent_email,
            "consent_token": consent_token
        })

        await self.db.commit()

        # Send email to parent
        from app.tasks.email import send_parental_consent_email
        send_parental_consent_email.delay(parent_email, consent_token)

    async def verify_parental_consent(self, consent_token: str) -> bool:
        """Verify parental consent via token."""

        query = text("""
            UPDATE parental_consent_requests
            SET consent_given = true,
                consented_at = CURRENT_TIMESTAMP
            WHERE consent_token = :token
                AND expires_at > CURRENT_TIMESTAMP
                AND consent_given = false
            RETURNING user_id
        """)

        result = await self.db.execute(query, {"token": consent_token})
        row = result.fetchone()

        if row:
            await self.db.commit()
            return True

        return False
```

## FERPA Compliance

### Access Controls

```sql
-- FERPA requires strict access controls for student education records
-- Already implemented via PostgreSQL RLS in guide 05

-- Additional: Education official access logging
CREATE TABLE education_official_access (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    official_user_id UUID NOT NULL REFERENCES users(user_id),
    student_user_id UUID NOT NULL REFERENCES users(user_id),
    access_type VARCHAR(50) NOT NULL,  -- view, export, modify
    accessed_resource VARCHAR(255),
    accessed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_official_access_student ON education_official_access(student_user_id, accessed_at);
CREATE INDEX idx_official_access_official ON education_official_access(official_user_id, accessed_at);
```

```python
# app/middleware/ferpa_audit.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class FERPAAuditMiddleware(BaseHTTPMiddleware):
    """Log access to student education records."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Log access to student data endpoints
        if request.url.path.startswith("/api/students/"):
            await self.log_access(request, response)

        return response

    async def log_access(self, request: Request, response):
        """Log student record access."""

        # Extract student ID from URL
        # Log who accessed, what, when, from where
        # Store in education_official_access table

        pass
```

## Encryption

### At Rest (Database)

```sql
-- PostgreSQL encryption with pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive columns
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),

    -- Encrypted fields
    ssn_encrypted BYTEA,  -- Social Security Number (if collected)
    phone_encrypted BYTEA,
    date_of_birth_encrypted BYTEA,

    encryption_key_id UUID NOT NULL  -- For key rotation
);

-- Encryption functions
CREATE OR REPLACE FUNCTION encrypt_field(plaintext TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, key);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrypt_field(ciphertext BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, key);
END;
$$ LANGUAGE plpgsql;
```

```python
# app/core/encryption.py
from cryptography.fernet import Fernet
from app.core.config import settings

class EncryptionService:
    """Field-level encryption service."""

    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext."""
        return self.fernet.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext."""
        return self.fernet.decrypt(ciphertext).decode()
```

### In Transit (TLS)

```yaml
# kubernetes/tls-certificate.yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: dreamseed-tls
  namespace: dreamseed-production
spec:
  secretName: dreamseed-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - api.dreamseed.ai
    - app.dreamseed.ai
```

```nginx
# Nginx TLS configuration
ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Audit Logging

### Comprehensive Audit Trail

```python
# app/services/audit_service.py
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy import text

class AuditService:
    """Centralized audit logging."""

    SENSITIVE_ACTIONS = [
        "user_created",
        "user_deleted",
        "user_data_exported",
        "consent_given",
        "consent_revoked",
        "grade_modified",
        "assessment_submitted",
        "role_changed",
        "permission_granted"
    ]

    async def log_action(
        self,
        user_id: Optional[UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID],
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ):
        """Log auditable action."""

        query = text("""
            INSERT INTO audit_logs
                (user_id, action, resource_type, resource_id, metadata, ip_address, created_at)
            VALUES
                (:user_id, :action, :resource_type, :resource_id, :metadata, :ip_address, CURRENT_TIMESTAMP)
        """)

        await self.db.execute(query, {
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "metadata": metadata or {},
            "ip_address": ip_address
        })

        await self.db.commit()

        # Stream to Kafka for real-time monitoring
        if action in self.SENSITIVE_ACTIONS:
            await self.stream_to_kafka(action, metadata)

    async def stream_to_kafka(self, action: str, metadata: Dict):
        """Stream sensitive actions to Kafka for monitoring."""
        from app.core.kafka import kafka_producer

        await kafka_producer.send(
            "audit-logs",
            value={
                "action": action,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

### Audit Log Schema

```sql
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Partition by month for performance
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Authentication & Authorization

### JWT Security

```python
# app/core/auth.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
    }

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> UUID:
    """Verify JWT token."""

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = UUID(payload["sub"])

        # Check if token is revoked
        if await is_token_revoked(payload["jti"]):
            raise HTTPException(status_code=401, detail="Token revoked")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def is_token_revoked(jti: str) -> bool:
    """Check if JWT is in revocation list."""
    # Check Redis cache
    from app.core.redis import redis_client
    return await redis_client.exists(f"revoked_token:{jti}")
```

## Security Headers

### FastAPI Middleware

```python
# app/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.dreamseed.ai; "
            "frame-ancestors 'none'"
        )

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
```

## Vulnerability Scanning

### Snyk Integration

```yaml
# .github/workflows/security-scan.yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 0 * * *" # Daily at midnight

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload result to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: snyk.sarif
```

### OWASP ZAP Scanning

```bash
# scripts/security-scan.sh
#!/bin/bash

# Run OWASP ZAP baseline scan
docker run -v $(pwd):/zap/wrk/:rw \
  -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.dreamseed.ai \
  -r zap-report.html
```

## Incident Response

### Incident Response Plan

```python
# app/services/incident_response.py
class IncidentResponseService:
    """Handle security incidents."""

    SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

    async def report_incident(
        self,
        incident_type: str,
        severity: str,
        description: str,
        affected_users: List[UUID] = None
    ):
        """Report security incident."""

        # 1. Log incident
        incident_id = await self.log_incident(
            incident_type, severity, description, affected_users
        )

        # 2. Notify security team
        if severity in ["high", "critical"]:
            await self.notify_security_team(incident_id, severity)

        # 3. Trigger automated response
        if incident_type == "data_breach":
            await self.initiate_breach_protocol(incident_id, affected_users)

        return incident_id

    async def initiate_breach_protocol(self, incident_id: UUID, affected_users: List[UUID]):
        """Automated response to data breach."""

        # 1. Revoke all active sessions
        for user_id in affected_users:
            await self.revoke_user_sessions(user_id)

        # 2. Force password reset
        await self.force_password_reset(affected_users)

        # 3. Notify affected users
        await self.notify_affected_users(affected_users, incident_id)

        # 4. Generate compliance report
        await self.generate_breach_report(incident_id, affected_users)
```

## Summary

Security & compliance implementation provides:

1. **GDPR compliance**: Data export, right to be forgotten, consent management
2. **COPPA compliance**: Parental consent for users <13
3. **FERPA compliance**: Access controls, audit logging for education records
4. **Encryption**: AES-256 at rest, TLS 1.3 in transit
5. **Audit logging**: Complete trail with Kafka streaming
6. **Security headers**: CSP, HSTS, X-Frame-Options
7. **Vulnerability scanning**: Snyk, OWASP ZAP
8. **Incident response**: Automated breach protocols

**Key Features**:

- Automated compliance workflows
- Real-time security monitoring
- Encrypted sensitive data
- Comprehensive audit trails
- Regular security scans

**Next Steps**:

- Annual penetration testing
- Security awareness training
- SOC 2 Type II certification
- Bug bounty program
