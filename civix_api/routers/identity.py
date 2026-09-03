from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel
from datetime import datetime
import json

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser

router = APIRouter(
    prefix="/api/v1/identity",
    tags=["identity"]
)

class IdentityResolutionRequest(BaseModel):
    source_identity_id: UUID
    person_id: Optional[UUID] = None
    candidate_id: Optional[UUID] = None
    decision: str  # ACCEPTED | REJECTED
    decision_notes: str

class IdentityResolutionResponse(BaseModel):
    resolution_id: UUID
    source_identity_id: UUID
    candidate_id: Optional[UUID] = None
    resolved_person_id: Optional[UUID] = None
    status: str
    decision_notes: Optional[str] = None

@router.get("/candidates")
async def list_candidates(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    res = await session.execute(text("""
        SELECT 
            candidate_id, 
            source_identity_id, 
            proposed_person_id,
            matching_rule_id,
            deterministic_signals,
            supporting_evidence_ids,
            created_at
        FROM civix.identity_candidate
        WHERE is_active = TRUE
    """))
    candidates = []
    for row in res.fetchall():
        candidates.append({
            "candidate_id": row.candidate_id,
            "source_identity_id": row.source_identity_id,
            "proposed_person_id": row.proposed_person_id,
            "matching_rule_id": row.matching_rule_id,
            "deterministic_signals": row.deterministic_signals,
            "supporting_evidence_ids": row.supporting_evidence_ids,
            "created_at": row.created_at
        })
    return {"candidates": candidates}

@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    res = await session.execute(text("""
        SELECT 
            candidate_id, 
            source_identity_id, 
            proposed_person_id,
            matching_rule_id,
            deterministic_signals,
            supporting_evidence_ids,
            created_at
        FROM civix.identity_candidate
        WHERE candidate_id = :cid
    """), {"cid": candidate_id})
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "candidate_id": row.candidate_id,
        "source_identity_id": row.source_identity_id,
        "proposed_person_id": row.proposed_person_id,
        "matching_rule_id": row.matching_rule_id,
        "deterministic_signals": row.deterministic_signals,
        "supporting_evidence_ids": row.supporting_evidence_ids,
        "created_at": row.created_at
    }

@router.post("/resolve", response_model=IdentityResolutionResponse)
async def resolve_identity(
    req: IdentityResolutionRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    # 1. RBAC check
    if user.role not in ("SUPERVISOR", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPERVISOR or ADMIN can perform identity resolution."
        )

    # 2. Validation
    if req.decision not in ("ACCEPTED", "REJECTED"):
        raise HTTPException(status_code=422, detail="decision must be ACCEPTED or REJECTED")
        
    if req.decision == "ACCEPTED" and req.person_id is None:
        raise HTTPException(status_code=422, detail="person_id is required for ACCEPTED")
        
    if req.decision == "REJECTED" and req.person_id is not None:
        raise HTTPException(status_code=422, detail="person_id must be NULL for REJECTED")
        
    if not req.decision_notes or not req.decision_notes.strip():
        raise HTTPException(status_code=422, detail="decision_notes is required")

    # 3. Transaction
    # Lock source identity
    lock_result = await session.execute(
        text("SELECT entity_id FROM civix.source_identity WHERE entity_id = :sid FOR UPDATE"),
        {"sid": req.source_identity_id}
    )
    if not lock_result.first():
        raise HTTPException(status_code=404, detail="Source identity not found")
        
    # Check if target person exists when ACCEPTED
    if req.decision == "ACCEPTED":
        person_res = await session.execute(
            text("SELECT entity_id FROM civix.person WHERE entity_id = :pid"),
            {"pid": req.person_id}
        )
        if not person_res.first():
            raise HTTPException(status_code=404, detail="Person not found")
            
    # Check candidate if provided
    if req.candidate_id:
        cand_res = await session.execute(
            text("SELECT candidate_id FROM civix.identity_candidate WHERE candidate_id = :cid"),
            {"cid": req.candidate_id}
        )
        if not cand_res.first():
            raise HTTPException(status_code=404, detail="Candidate not found")

    # Check for active ACCEPTED resolution to prevent conflicting resolutions
    active_res = await session.execute(
        text("""
            SELECT resolution_id, resolved_person_id, status 
            FROM civix.identity_resolution 
            WHERE source_identity_id = :sid 
            AND superseded_by IS NULL
        """),
        {"sid": req.source_identity_id}
    )
    active_records = active_res.fetchall()
    
    if req.decision == "ACCEPTED":
        for rec in active_records:
            if rec.status == "ACCEPTED" and rec.resolved_person_id != req.person_id:
                raise HTTPException(
                    status_code=409, 
                    detail="Conflicting active ACCEPTED resolution exists for this source identity."
                )

    new_res_id = uuid4()
    
    # Insert new resolution
    await session.execute(
        text("""
            INSERT INTO civix.identity_resolution (
                resolution_id, source_identity_id, candidate_id, resolved_person_id,
                status, decided_by, decision_notes, tx_start
            ) VALUES (
                :rid, :sid, :cid, :pid, :status, :uid, :notes, :now
            )
        """),
        {
            "rid": new_res_id,
            "sid": req.source_identity_id,
            "cid": req.candidate_id,
            "pid": req.person_id if req.decision == "ACCEPTED" else None,
            "status": req.decision,
            "uid": user.user_id,
            "notes": req.decision_notes,
            "now": datetime.utcnow()
        }
    )
    
    # Insert audit event
    audit_metadata = {
        "source_identity_id": str(req.source_identity_id),
        "resolved_person_id": str(req.person_id) if req.person_id else None,
        "candidate_id": str(req.candidate_id) if req.candidate_id else None,
        "decision": req.decision
    }
    
    await session.execute(
        text("""
            INSERT INTO civix.audit_event (
                audit_id, user_id, action, target_table, target_id, case_context_id, timestamp, metadata
            ) VALUES (
                :aid, :uid, 'IDENTITY_RESOLVE', 'identity_resolution', :tid, NULL, :now, CAST(:meta AS jsonb)
            )
        """),
        {
            "aid": uuid4(),
            "uid": user.user_id,
            "tid": new_res_id,
            "now": datetime.utcnow(),
            "meta": json.dumps(audit_metadata)
        }
    )
    
    await session.commit()
    
    return IdentityResolutionResponse(
        resolution_id=new_res_id,
        source_identity_id=req.source_identity_id,
        candidate_id=req.candidate_id,
        resolved_person_id=req.person_id if req.decision == "ACCEPTED" else None,
        status=req.decision,
        decision_notes=req.decision_notes
    )
