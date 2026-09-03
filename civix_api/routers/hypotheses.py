from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from uuid import UUID
from datetime import datetime

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["hypotheses"]
)

class HypothesisCreateRequest(BaseModel):
    hypothesis_text: str

class HypothesisResponse(BaseModel):
    hypothesis_id: UUID
    hypothesis_text: str
    status: str
    created_by: UUID
    tx_start: datetime

@router.post("/{case_id}/hypotheses", response_model=HypothesisResponse)
async def create_hypothesis(
    case_id: UUID,
    hypothesis_data: HypothesisCreateRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    # Verify case access
    result = await session.execute(
        text("SELECT status FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": case_id}
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found or access denied."
        )

    # Insert Hypothesis
    insert_result = await session.execute(
        text("""
            INSERT INTO civix.hypothesis (case_id, hypothesis_text, created_by)
            VALUES (:cid, :txt, :uid)
            RETURNING hypothesis_id, hypothesis_text, status, created_by, tx_start
        """),
        {
            "cid": case_id,
            "txt": hypothesis_data.hypothesis_text,
            "uid": user.user_id
        }
    )
    row = insert_result.first()
    
    return HypothesisResponse(
        hypothesis_id=row[0],
        hypothesis_text=row[1],
        status=row[2],
        created_by=row[3],
        tx_start=row[4]
    )

@router.get("/{case_id}/hypotheses", response_model=List[HypothesisResponse])
async def list_hypotheses(
    case_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    # Verify case access
    case_check = await session.execute(
        text("SELECT status FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": case_id}
    )
    if not case_check.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found or access denied."
        )

    # Fetch active hypotheses
    result = await session.execute(
        text("""
            SELECT hypothesis_id, hypothesis_text, status, created_by, tx_start
            FROM civix.hypothesis
            WHERE case_id = :cid AND tx_end IS NULL
            ORDER BY tx_start DESC
        """),
        {"cid": case_id}
    )
    
    hypotheses = []
    for row in result.fetchall():
        hypotheses.append(HypothesisResponse(
            hypothesis_id=row[0],
            hypothesis_text=row[1],
            status=row[2],
            created_by=row[3],
            tx_start=row[4]
        ))
    return hypotheses
