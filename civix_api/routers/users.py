from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

@router.get("/me")
async def get_current_user(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    # We query the DB again within the RLS session just to return the full profile
    # The requirement: Return only the authenticated user's own record.
    # We query civix_user which is not strictly RLS'd but we filter by the authenticated user's ID.
    result = await session.execute(
        text("""
            SELECT user_id, username, display_name, role, clearance_level, external_auth_id
            FROM civix.civix_user 
            WHERE user_id = :uid
        """),
        {"uid": user.user_id}
    )
    user_row = result.first()
    if not user_row:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return {
        "user_id": str(user_row[0]),
        "username": user_row[1],
        "display_name": user_row[2],
        "role": user_row[3],
        "clearance_level": user_row[4],
        "external_auth_id": user_row[5]
    }
