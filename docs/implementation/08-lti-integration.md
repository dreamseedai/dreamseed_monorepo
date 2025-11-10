# LTI 1.3 Integration

## Table of Contents

- [Overview](#overview)
- [LTI 1.3 Architecture](#lti-13-architecture)
- [Platform Registration](#platform-registration)
- [Authentication Flow](#authentication-flow)
- [Deep Linking](#deep-linking)
- [Grade Passback](#grade-passback)
- [Names and Roles Service](#names-and-roles-service)
- [Implementation](#implementation)
- [Testing Strategy](#testing-strategy)

## Overview

LTI (Learning Tools Interoperability) 1.3 enables seamless integration with Learning Management Systems (LMS):

- **Single Sign-On**: Students/teachers launch from LMS without separate login
- **Deep Linking**: Embed DreamSeedAI content in LMS courses
- **Grade Passback**: Send assessment scores back to LMS gradebook
- **Roster Sync**: Automatically sync class enrollment from LMS

**Supported Platforms**: Canvas, Moodle, Blackboard, Brightspace, Google Classroom

## LTI 1.3 Architecture

### Key Components

```
LMS (Platform)                          DreamSeedAI (Tool)
│                                       │
│ 1. Launch Request (OIDC)             │
├──────────────────────────────────────>│
│                                       │ 2. Validate JWT
│                                       │ 3. Create/link user
│                                       │
│ 4. Redirect to content                │
│<──────────────────────────────────────┤
│                                       │
│ 5. User interacts                     │
│                                       │
│ 6. Score available                    │
│<─────── Grade passback ───────────────┤
```

### Database Schema

```sql
-- LTI Platform registrations
CREATE TABLE lti_platforms (
    platform_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    platform_name VARCHAR(100) NOT NULL,  -- Canvas, Moodle, etc.
    issuer VARCHAR(255) NOT NULL UNIQUE,  -- LMS issuer URL
    auth_endpoint VARCHAR(500) NOT NULL,
    token_endpoint VARCHAR(500) NOT NULL,
    jwks_endpoint VARCHAR(500) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    deployment_id VARCHAR(255),
    public_key TEXT,  -- LMS public key for JWT validation
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lti_platforms_org ON lti_platforms(organization_id);
CREATE INDEX idx_lti_platforms_issuer ON lti_platforms(issuer);

-- LTI Launch sessions
CREATE TABLE lti_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES lti_platforms(platform_id),
    user_id UUID REFERENCES users(user_id),
    lti_user_id VARCHAR(255) NOT NULL,  -- LMS user ID
    resource_link_id VARCHAR(255),  -- Assignment/resource ID in LMS
    context_id VARCHAR(255),  -- Course ID in LMS
    roles TEXT[],  -- Instructor, Learner, etc.
    launch_data JSONB,  -- Full LTI claim data
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_lti_sessions_platform ON lti_sessions(platform_id);
CREATE INDEX idx_lti_sessions_user ON lti_sessions(user_id);
CREATE INDEX idx_lti_sessions_resource ON lti_sessions(resource_link_id);

-- Grade passback configuration
CREATE TABLE lti_grade_sync (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_id UUID NOT NULL REFERENCES lti_platforms(platform_id),
    assessment_id UUID NOT NULL REFERENCES assessments(assessment_id),
    resource_link_id VARCHAR(255) NOT NULL,
    line_item_url VARCHAR(500),  -- AGS line item URL
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, resource_link_id, assessment_id)
);
```

## Platform Registration

### Manual Registration Process

```python
# app/services/lti_service.py
from typing import Dict
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from jose import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class LTIService:
    """LTI 1.3 integration service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_platform(
        self,
        organization_id: UUID,
        platform_name: str,
        issuer: str,
        auth_endpoint: str,
        token_endpoint: str,
        jwks_endpoint: str,
        client_id: str,
        deployment_id: str = None
    ) -> UUID:
        """Register an LTI platform (LMS)."""

        # Fetch public key from JWKS endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_endpoint)
            jwks = response.json()

        # Store first key (simplified - should store all keys)
        public_key_jwk = jwks["keys"][0]

        query = text("""
            INSERT INTO lti_platforms
                (organization_id, platform_name, issuer, auth_endpoint,
                 token_endpoint, jwks_endpoint, client_id, deployment_id, public_key)
            VALUES
                (:org_id, :platform_name, :issuer, :auth_endpoint,
                 :token_endpoint, :jwks_endpoint, :client_id, :deployment_id, :public_key)
            RETURNING platform_id
        """)

        result = await self.db.execute(query, {
            "org_id": str(organization_id),
            "platform_name": platform_name,
            "issuer": issuer,
            "auth_endpoint": auth_endpoint,
            "token_endpoint": token_endpoint,
            "jwks_endpoint": jwks_endpoint,
            "client_id": client_id,
            "deployment_id": deployment_id,
            "public_key": str(public_key_jwk)
        })

        await self.db.commit()

        row = result.fetchone()
        return row.platform_id
```

## Authentication Flow

### OIDC Login Initiation

```python
# app/api/endpoints/lti.py
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.lti_service import LTIService

router = APIRouter(prefix="/lti", tags=["lti"])

@router.post("/login")
async def lti_login(
    iss: str = Form(...),
    login_hint: str = Form(...),
    target_link_uri: str = Form(...),
    lti_message_hint: str = Form(None),
    client_id: str = Form(...),
    lti_deployment_id: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """OIDC login initiation (step 1)."""

    # Get platform configuration
    lti_service = LTIService(db)
    platform = await lti_service.get_platform_by_issuer(iss)

    if not platform:
        raise HTTPException(status_code=404, detail="Platform not registered")

    # Generate state and nonce
    import secrets
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    # Store state/nonce in session/cache
    # (In production, use Redis with expiration)

    # Build OIDC auth request
    auth_params = {
        "response_type": "id_token",
        "response_mode": "form_post",
        "scope": "openid",
        "client_id": client_id,
        "redirect_uri": f"{settings.BACKEND_URL}/lti/launch",
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "prompt": "none"
    }

    if lti_message_hint:
        auth_params["lti_message_hint"] = lti_message_hint

    # Redirect to platform's auth endpoint
    from urllib.parse import urlencode
    auth_url = f"{platform.auth_endpoint}?{urlencode(auth_params)}"

    return RedirectResponse(url=auth_url, status_code=302)

@router.post("/launch")
async def lti_launch(
    request: Request,
    id_token: str = Form(...),
    state: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """LTI launch (step 2) - validate JWT and create session."""

    lti_service = LTIService(db)

    # Decode JWT header to get issuer
    import json
    import base64

    header = json.loads(base64.urlsafe_b64decode(id_token.split('.')[0] + '=='))

    # Get platform by kid (key ID)
    platform = await lti_service.get_platform_by_kid(header.get('kid'))

    if not platform:
        raise HTTPException(status_code=401, detail="Invalid platform")

    # Validate JWT
    try:
        claims = jwt.decode(
            id_token,
            platform.public_key,
            algorithms=["RS256"],
            audience=platform.client_id
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")

    # Validate LTI claims
    if claims.get("https://purl.imsglobal.org/spec/lti/claim/message_type") != "LtiResourceLinkRequest":
        raise HTTPException(status_code=400, detail="Invalid message type")

    # Extract user info
    lti_user_id = claims["sub"]
    email = claims.get("email")
    name = claims.get("name", "")
    roles = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])

    # Get or create user
    user = await lti_service.get_or_create_user(
        platform_id=platform.platform_id,
        lti_user_id=lti_user_id,
        email=email,
        name=name,
        roles=roles
    )

    # Create LTI session
    session_id = await lti_service.create_session(
        platform_id=platform.platform_id,
        user_id=user.user_id,
        lti_user_id=lti_user_id,
        resource_link_id=claims.get("https://purl.imsglobal.org/spec/lti/claim/resource_link", {}).get("id"),
        context_id=claims.get("https://purl.imsglobal.org/spec/lti/claim/context", {}).get("id"),
        roles=roles,
        launch_data=claims
    )

    # Generate auth token for user
    from app.core.auth import create_access_token
    access_token = create_access_token(user.user_id)

    # Redirect to frontend with token
    target_url = f"{settings.FRONTEND_URL}/lti/session?token={access_token}&session_id={session_id}"

    return RedirectResponse(url=target_url, status_code=302)
```

## Deep Linking

### Content Selection

```python
@router.get("/content-select")
async def content_select(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Present content selection UI for deep linking."""

    # Get LTI session
    session = await get_lti_session(db, session_id)

    # Verify this is a deep linking request
    launch_data = session.launch_data
    if launch_data.get("https://purl.imsglobal.org/spec/lti/claim/message_type") != "LtiDeepLinkingRequest":
        raise HTTPException(status_code=400, detail="Not a deep linking request")

    # Return available content
    # (Frontend will render selection UI)
    assessments = await get_available_assessments(db, session.user_id)

    return {
        "session_id": str(session_id),
        "deep_link_return_url": launch_data.get("https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings", {}).get("deep_link_return_url"),
        "assessments": assessments
    }

@router.post("/deep-link-return")
async def deep_link_return(
    session_id: UUID,
    selected_content_ids: list[UUID],
    db: AsyncSession = Depends(get_db)
):
    """Return selected content to LMS via deep linking."""

    lti_service = LTIService(db)
    session = await get_lti_session(db, session_id)

    # Build deep linking response JWT
    launch_data = session.launch_data
    deep_link_settings = launch_data.get("https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings", {})

    content_items = []
    for content_id in selected_content_ids:
        content = await get_content(db, content_id)

        content_items.append({
            "type": "ltiResourceLink",
            "title": content.title,
            "url": f"{settings.BACKEND_URL}/lti/launch?content_id={content_id}",
            "custom": {
                "content_id": str(content_id)
            }
        })

    # Create JWT
    deep_link_jwt = jwt.encode(
        {
            "iss": platform.client_id,
            "aud": platform.issuer,
            "exp": int(time.time()) + 600,
            "iat": int(time.time()),
            "nonce": secrets.token_urlsafe(16),
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": session.platform.deployment_id,
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": content_items,
            "https://purl.imsglobal.org/spec/lti-dl/claim/data": deep_link_settings.get("data")
        },
        settings.LTI_PRIVATE_KEY,
        algorithm="RS256"
    )

    # Return form that auto-submits to LMS
    return_url = deep_link_settings["deep_link_return_url"]

    return f"""
    <html>
    <body onload="document.forms[0].submit()">
        <form method="POST" action="{return_url}">
            <input type="hidden" name="JWT" value="{deep_link_jwt}"/>
        </form>
    </body>
    </html>
    """
```

## Grade Passback

### Assignment and Grade Service (AGS)

```python
# app/services/lti_grade_service.py
import httpx
from typing import Optional
from uuid import UUID
from sqlalchemy import text

class LTIGradeService:
    """LTI Advantage Grade Service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_access_token(self, platform_id: UUID) -> str:
        """Get OAuth 2.0 access token for AGS."""
        platform = await self.get_platform(platform_id)

        # Request token from platform
        async with httpx.AsyncClient() as client:
            response = await client.post(
                platform.token_endpoint,
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": self._build_client_assertion(platform),
                    "scope": "https://purl.imsglobal.org/spec/lti-ags/scope/score"
                }
            )

            data = response.json()
            return data["access_token"]

    def _build_client_assertion(self, platform) -> str:
        """Build JWT client assertion for OAuth."""
        import time

        return jwt.encode(
            {
                "iss": platform.client_id,
                "sub": platform.client_id,
                "aud": platform.token_endpoint,
                "iat": int(time.time()),
                "exp": int(time.time()) + 300,
                "jti": secrets.token_urlsafe(16)
            },
            settings.LTI_PRIVATE_KEY,
            algorithm="RS256"
        )

    async def send_score(
        self,
        session_id: UUID,
        score: float,
        max_score: float = 1.0,
        comment: str = None
    ):
        """Send score to LMS gradebook."""

        # Get session and line item URL
        session = await self.get_session(session_id)
        launch_data = session.launch_data

        ags_claim = launch_data.get("https://purl.imsglobal.org/spec/lti-ags/claim/endpoint", {})
        line_item_url = ags_claim.get("lineitem")

        if not line_item_url:
            # No gradebook integration
            return False

        # Get access token
        access_token = await self.get_access_token(session.platform_id)

        # Send score
        score_url = f"{line_item_url}/scores"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                score_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/vnd.ims.lis.v1.score+json"
                },
                json={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "scoreGiven": score,
                    "scoreMaximum": max_score,
                    "comment": comment,
                    "activityProgress": "Completed",
                    "gradingProgress": "FullyGraded",
                    "userId": session.lti_user_id
                }
            )

            return response.status_code == 200
```

## Names and Roles Service

### Roster Sync

```python
# app/services/lti_nrps_service.py
class LTINRPSService:
    """LTI Names and Roles Provisioning Service."""

    async def sync_roster(self, session_id: UUID):
        """Sync class roster from LMS."""

        session = await self.get_session(session_id)
        launch_data = session.launch_data

        nrps_claim = launch_data.get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {})
        context_memberships_url = nrps_claim.get("context_memberships_url")

        if not context_memberships_url:
            return []

        # Get access token
        access_token = await self.get_access_token(session.platform_id, scope="https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly")

        # Fetch roster
        async with httpx.AsyncClient() as client:
            response = await client.get(
                context_memberships_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            data = response.json()
            members = data.get("members", [])

        # Create/update users
        for member in members:
            await self.get_or_create_user(
                platform_id=session.platform_id,
                lti_user_id=member["user_id"],
                email=member.get("email"),
                name=member.get("name"),
                roles=member.get("roles", [])
            )

        return members
```

## Testing Strategy

```python
# tests/test_lti_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.lti_service import LTIService

@pytest.mark.asyncio
async def test_lti_launch_validation(db_session):
    """Test LTI launch JWT validation."""
    service = LTIService(db_session)

    # Create test JWT
    # Validate claims
    # Verify user creation
    pass

@pytest.mark.asyncio
async def test_grade_passback(db_session):
    """Test AGS grade passback."""
    from app.services.lti_grade_service import LTIGradeService

    grade_service = LTIGradeService(db_session)

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)

        success = await grade_service.send_score(
            session_id=uuid4(),
            score=0.85,
            max_score=1.0
        )

        assert success
        mock_post.assert_called()
```

## Summary

LTI 1.3 integration provides:

1. **SSO**: Seamless login from LMS platforms
2. **Deep Linking**: Embed content in LMS courses
3. **Grade Passback**: Automatic score sync to LMS gradebook
4. **Roster Sync**: Import class enrollment from LMS
5. **Multi-platform**: Supports Canvas, Moodle, Blackboard, etc.

**Key Standards**:

- LTI 1.3 Core
- LTI Advantage (AGS, NRPS, Deep Linking)
- OAuth 2.0 / OIDC

**Next Steps**:

- Implement automated platform registration
- Add assignment creation via AGS
- Support LTI resource selection
- Build admin UI for platform management
