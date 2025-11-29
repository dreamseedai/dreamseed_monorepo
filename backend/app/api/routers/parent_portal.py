"""
Parent portal API - Children and report access

Endpoints:
- GET /api/parent/children: Get list of parent's children
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session  # alias for get_async_db
from app.core.security import get_current_parent
from app.models.parent_models import ParentChildLink
from app.models.user import User
from app.schemas.parent_schemas import ParentChild, ParentChildrenResponse


# Type conversion helpers
def user_id_to_uuid(user_id: Any) -> UUID:
    """Convert integer user ID to UUID format for API responses"""
    # Accepts Column[int] or int at runtime
    return UUID(int=int(user_id))


router = APIRouter(prefix="/api/parent", tags=["parent"])


@router.get("/children", response_model=ParentChildrenResponse)
async def get_parent_children(
    db: AsyncSession = Depends(get_async_session),
    parent: User = Depends(get_current_parent),
):
    """
    Get list of children linked to current parent.

    Returns:
    - List of children with basic info (id, name, school, grade)
    - Used for dropdown in parent report download page
    """
    # Get parent-child links
    links_query = select(ParentChildLink).where(ParentChildLink.parent_id == parent.id)
    links_result = await db.execute(links_query)
    links = links_result.scalars().all()

    if not links:
        return ParentChildrenResponse(parentId=user_id_to_uuid(parent.id), children=[])

    child_ids = [link.child_id for link in links]

    # Get child user details
    users_query = select(User).where(User.id.in_(child_ids))
    users_result = await db.execute(users_query)
    users = users_result.scalars().all()

    # Build response
    children: list[ParentChild] = []
    for user in users:
        children.append(
            ParentChild(
                id=user_id_to_uuid(user.id),
                name=user.email.split("@")[0],  # TODO: Use profile.name when available
                school=None,  # TODO: Join with StudentOrgEnrollment
                grade=None,  # TODO: Add to user profile
            )
        )

    return ParentChildrenResponse(
        parentId=user_id_to_uuid(parent.id), children=children
    )
