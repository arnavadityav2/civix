from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json
from pydantic import BaseModel

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.services.feature_extractor import extract_candidate_features
from civix_api.services.ml_service import get_ml_service, MLService, EXPECTED_FEATURES
from civix_api.services.intelligence_engine import generate_lead_for_entity

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["leads"]
)

class GenerateLeadsRequest(BaseModel):
    hypothesis_id: Optional[UUID] = None

class InvestigativeLeadResponse(BaseModel):
    lead_id: UUID
    case_id: UUID
    target_entity_id: UUID
    hypothesis_id: Optional[UUID] = None
    generated_by_run_id: Optional[UUID] = None
    generated_by_person: Optional[UUID] = None
    ai_confidence: Optional[float] = None
    lead_text: str
    priority: str
    status: str
    # C3 fields
    explanation_status: Optional[str] = None
    feature_vector_version: Optional[str] = None
    finding_count: Optional[int] = None

class GenerateLeadsResponse(BaseModel):
    case_id: UUID
    model_version: str
    feature_vector_version: str
    limitations: List[str]
    leads: List[InvestigativeLeadResponse]
    message: Optional[str] = None

class FindingResponse(BaseModel):
    finding_id: UUID
    finding_type: str
    subject_entity_id: UUID
    object_entity_id: Optional[UUID] = None
    relationship_strength: str
    key_facts: List[str]
    path_description: Optional[str] = None
    hop_count: int
    matching_rule_id: Optional[str] = None
    suppressed: bool
    suppression_reason: Optional[str] = None

class ModelMetadataResponse(BaseModel):
    model_name: str
    model_version: str
    feature_count: int
    feature_names: List[str]
    feature_vector_version: str

@router.get("/{case_id}/leads", response_model=List[InvestigativeLeadResponse])
async def get_case_leads(
    case_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Retrieve persisted investigative leads for the case.
    C3: Includes explanation_status, feature_vector_version, finding_count.
    """
    # 1. Verify case access
    result = await session.execute(
        text("SELECT status FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": case_id}
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found or access denied."
        )

    # 2. Fetch leads including C3 columns
    result = await session.execute(
        text("""
            SELECT il.lead_id, il.case_id, il.target_entity_id, il.hypothesis_id,
                   il.generated_by_run_id, il.generated_by_person, il.ai_confidence,
                   il.lead_text, il.priority, il.status,
                   il.explanation_status, il.feature_vector_version,
                   (SELECT COUNT(*) FROM civix.investigative_finding f WHERE f.lead_id = il.lead_id) AS finding_count
            FROM civix.investigative_lead il
            WHERE il.case_id = :cid
            ORDER BY il.ai_confidence DESC NULLS LAST
        """),
        {"cid": case_id}
    )
    
    leads = []
    for row in result.fetchall():
        leads.append(InvestigativeLeadResponse(
            lead_id=row.lead_id,
            case_id=row.case_id,
            target_entity_id=row.target_entity_id,
            hypothesis_id=row.hypothesis_id,
            generated_by_run_id=row.generated_by_run_id,
            generated_by_person=row.generated_by_person,
            ai_confidence=float(row.ai_confidence) if row.ai_confidence is not None else None,
            lead_text=row.lead_text,
            priority=row.priority,
            status=row.status,
            explanation_status=row.explanation_status,
            feature_vector_version=row.feature_vector_version,
            finding_count=int(row.finding_count) if row.finding_count is not None else 0,
        ))
        
    return leads


@router.post("/{case_id}/leads/generate", response_model=GenerateLeadsResponse)
async def generate_case_leads(
    case_id: UUID,
    req: GenerateLeadsRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    """
    C3 Intelligence Engine: runs deterministic findings → 70-feature XGBoost →
    Gemini explanation → zero-hallucination validation → persists ranked leads.
    Replaces the previous hardcoded placeholder lead text.
    """
    from civix_api.services.intelligence_engine import FEATURE_VECTOR_VERSION

    # 1. Verify case access
    result = await session.execute(
        text("SELECT status FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": case_id}
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found or access denied."
        )

    # 2. Candidate Resolution: Find all PERSON entities linked to this case
    result = await session.execute(
        text("""
            SELECT cer.entity_id, p.display_name
            FROM civix.case_entity_role cer
            JOIN civix.person p ON p.entity_id = cer.entity_id
            WHERE cer.case_id = :cid
        """),
        {"cid": case_id}
    )
    candidates = [(str(row.entity_id), row.display_name) for row in result.fetchall()]
        
    if not candidates:
        return GenerateLeadsResponse(
            case_id=case_id,
            model_version="behavioral_xgboost_20260829T143327",
            feature_vector_version=FEATURE_VECTOR_VERSION,
            limitations=[
                "txn_type_diversity is zero-filled due to schema gap.",
                "Financial amounts and specific occupations may be zero-filled based on current synthetic data ingestion limitations."
            ],
            leads=[],
            message="No candidate persons found for this case."
        )

    # 3. Create analysis_run
    run_id = uuid4()
    try:
        await session.execute(
            text("""
                INSERT INTO civix.analysis_run (run_id, model_name, model_version, algorithm_type, started_at, initiated_by)
                VALUES (:rid, 'behavioral_xgboost', 'behavioral_xgboost_20260829T143327', 'XGBoost', :now, :uid)
            """),
            {"rid": run_id, "now": datetime.utcnow(), "uid": user.user_id}
        )
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foreign key or integrity violation: Ensure the hypothesis belongs to this case."
        )

    # 4. Run C3 Intelligence Engine for each candidate
    persisted_leads = []
    hypothesis_id_str = str(req.hypothesis_id) if req and req.hypothesis_id else None

    try:
        for entity_id, display_name in candidates:
            try:
                lead_result = await generate_lead_for_entity(
                    session=session,
                    subject_entity_id=entity_id,
                    case_id=str(case_id),
                    run_id=str(run_id),
                    user_id=str(user.user_id),
                    hypothesis_id=hypothesis_id_str,
                )
                persisted_leads.append(InvestigativeLeadResponse(
                    lead_id=UUID(lead_result.lead_id),
                    case_id=case_id,
                    target_entity_id=UUID(entity_id),
                    hypothesis_id=req.hypothesis_id if req else None,
                    generated_by_run_id=run_id,
                    generated_by_person=user.user_id,
                    ai_confidence=lead_result.ml_score,
                    lead_text=lead_result.lead_text,
                    priority=lead_result.priority,
                    status="OPEN",
                    explanation_status=lead_result.explanation_status,
                    feature_vector_version=FEATURE_VECTOR_VERSION,
                    finding_count=lead_result.finding_count,
                ))
            except Exception as e:
                err_str = str(e).lower()
                if "foreign key" in err_str or "integrity" in err_str:
                    await session.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Foreign key or integrity violation: Ensure the hypothesis belongs to this case."
                    )
                # Log and continue for other entity errors
                import logging
                logging.getLogger(__name__).error(f"C3 pipeline error for {entity_id}: {e}")

        await session.commit()

    except HTTPException:
        raise
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Foreign key or integrity violation: Ensure the hypothesis belongs to this case."
        )
    except Exception as e:
        await session.rollback()
        err_str = str(e).lower()
        if "foreign key" in err_str or "integrity" in err_str or "violates foreign key constraint" in err_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Foreign key or integrity violation: Ensure the hypothesis belongs to this case."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"C3 Intelligence Engine failed: {e}"
        )

    # Sort by score descending
    persisted_leads.sort(key=lambda l: l.ai_confidence or 0.0, reverse=True)

    return GenerateLeadsResponse(
        case_id=case_id,
        model_version="behavioral_xgboost_20260829T143327",
        feature_vector_version=FEATURE_VECTOR_VERSION,
        limitations=[
            "txn_type_diversity is zero-filled due to schema gap.",
            "Financial amounts and specific occupations may be zero-filled based on current synthetic data ingestion limitations.",
            "Gemini explanation may be SKIPPED if API is unavailable; deterministic findings and ML score remain valid.",
        ],
        leads=persisted_leads
    )

class LeadDispositionRequest(BaseModel):
    status: str
    disposition_notes: str

@router.post("/{case_id}/leads/{lead_id}/disposition", response_model=InvestigativeLeadResponse)
async def dispose_case_lead(
    case_id: UUID,
    lead_id: UUID,
    req: LeadDispositionRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Dispose an investigative lead (ADR-032).
    """
    valid_statuses = {"OPEN", "IN_PROGRESS", "CONFIRMED", "FALSE_POSITIVE", "CLOSED", "DEFERRED"}
    if req.status not in valid_statuses:
        raise HTTPException(status_code=422, detail="Invalid status")

    # 1. Verify case access (must have WRITE access)
    result = await session.execute(
        text("""
            SELECT permission_level 
            FROM civix.case_access 
            WHERE case_id = :cid AND user_id = :uid AND is_revoked = false
        """),
        {"cid": case_id, "uid": user.user_id}
    )
    access_row = result.first()
    if not access_row or access_row.permission_level not in ('WRITE', 'ADMIN'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Case not found or access denied."
        )

    # 2. Lock the Lead row (Case isolation enforced by case_id)
    result = await session.execute(
        text("""
            SELECT status 
            FROM civix.investigative_lead 
            WHERE lead_id = :lid AND case_id = :cid 
            FOR UPDATE
        """),
        {"lid": lead_id, "cid": case_id}
    )
    lead_row = result.first()
    if not lead_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lead not found or access denied."
        )

    current_status = lead_row.status

    # 3. Idempotency Check
    if current_status == req.status:
        # Return existing without mutating
        res = await session.execute(
            text("""
                SELECT lead_id, case_id, target_entity_id, hypothesis_id,
                       generated_by_run_id, generated_by_person, ai_confidence,
                       lead_text, priority, status
                FROM civix.investigative_lead
                WHERE lead_id = :lid
            """),
            {"lid": lead_id}
        )
        row = res.first()
        return InvestigativeLeadResponse(
            lead_id=row.lead_id, case_id=row.case_id, target_entity_id=row.target_entity_id,
            hypothesis_id=row.hypothesis_id, generated_by_run_id=row.generated_by_run_id,
            generated_by_person=row.generated_by_person, 
            ai_confidence=float(row.ai_confidence) if row.ai_confidence is not None else None,
            lead_text=row.lead_text, priority=row.priority, status=row.status
        )

    # 4. State Machine Validation
    terminal_states = {"CONFIRMED", "CLOSED", "FALSE_POSITIVE"}
    if current_status in terminal_states:
        raise HTTPException(status_code=409, detail="Lead is in a terminal state.")

    valid_transitions = {
        "OPEN": {"IN_PROGRESS", "CLOSED", "FALSE_POSITIVE"},
        "IN_PROGRESS": {"CONFIRMED", "FALSE_POSITIVE", "DEFERRED"},
        "DEFERRED": {"IN_PROGRESS"}
    }

    if req.status not in valid_transitions.get(current_status, set()):
        raise HTTPException(status_code=409, detail="Invalid state transition.")

    # 5. Update Lead
    try:
        now = datetime.utcnow()
        update_result = await session.execute(
            text("""
                UPDATE civix.investigative_lead
                SET status = :status,
                    disposition_notes = :notes,
                    disposed_by = :uid,
                    disposed_at = :now
                WHERE lead_id = :lid
                RETURNING lead_id, case_id, target_entity_id, hypothesis_id,
                          generated_by_run_id, generated_by_person, ai_confidence,
                          lead_text, priority, status
            """),
            {
                "status": req.status,
                "notes": req.disposition_notes,
                "uid": user.user_id,
                "now": now,
                "lid": lead_id
            }
        )
        updated_row = update_result.first()

        # 6. Insert Audit Event
        metadata = {
            "previous_status": current_status,
            "new_status": req.status,
            "disposition_notes": req.disposition_notes
        }
        await session.execute(
            text("""
                INSERT INTO civix.audit_event (
                    user_id, action, target_table, target_id, case_context_id, metadata
                ) VALUES (
                    :uid, 'LEAD_DISPOSITION', 'investigative_lead', :lid, :cid, :meta
                )
            """),
            {
                "uid": user.user_id,
                "lid": lead_id,
                "cid": case_id,
                "meta": json.dumps(metadata)
            }
        )

        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispose lead: {str(e)}"
        )

    return InvestigativeLeadResponse(
        lead_id=updated_row.lead_id,
        case_id=updated_row.case_id,
        target_entity_id=updated_row.target_entity_id,
        hypothesis_id=updated_row.hypothesis_id,
        generated_by_run_id=updated_row.generated_by_run_id,
        generated_by_person=updated_row.generated_by_person,
        ai_confidence=float(updated_row.ai_confidence) if updated_row.ai_confidence is not None else None,
        lead_text=updated_row.lead_text,
        priority=updated_row.priority,
        status=updated_row.status
    )


# =============================================================================
# C3-T08 — Read APIs: findings, explanation, provenance, model metadata
# =============================================================================

@router.get("/{case_id}/leads/{lead_id}/findings", response_model=List[FindingResponse])
async def get_lead_findings(
    case_id: UUID,
    lead_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    C3-T08: Return all deterministic findings for a lead.
    Distinguishes deterministic facts from ML score and LLM explanation.
    """
    lead_check = await session.execute(
        text("SELECT lead_id FROM civix.investigative_lead WHERE lead_id = :lid AND case_id = :cid"),
        {"lid": lead_id, "cid": case_id},
    )
    if not lead_check.first():
        raise HTTPException(status_code=404, detail="Lead not found or access denied.")

    result = await session.execute(
        text("""
            SELECT finding_id, finding_type, subject_entity_id, object_entity_id,
                   relationship_strength, key_facts, path_description,
                   hop_count, matching_rule_id, suppressed, suppression_reason
            FROM civix.investigative_finding
            WHERE lead_id = :lid
            ORDER BY created_at
        """),
        {"lid": lead_id},
    )
    out = []
    for row in result.fetchall():
        kf = row.key_facts
        if isinstance(kf, str):
            try:
                kf = json.loads(kf)
            except Exception:
                kf = [kf]
        out.append(FindingResponse(
            finding_id=row.finding_id,
            finding_type=row.finding_type,
            subject_entity_id=row.subject_entity_id,
            object_entity_id=row.object_entity_id,
            relationship_strength=row.relationship_strength,
            key_facts=kf or [],
            path_description=row.path_description,
            hop_count=row.hop_count,
            matching_rule_id=row.matching_rule_id,
            suppressed=row.suppressed,
            suppression_reason=row.suppression_reason,
        ))
    return out


@router.get("/{case_id}/leads/{lead_id}/explanation")
async def get_lead_explanation(
    case_id: UUID,
    lead_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    C3-T08: Return the validated Gemini explanation and its status.
    Distinguishes LLM output from deterministic findings and ML score.
    """
    result = await session.execute(
        text("""
            SELECT il.lead_id, il.explanation, il.explanation_status,
                   il.ai_confidence, il.feature_vector_version, il.lead_text
            FROM civix.investigative_lead il
            WHERE il.lead_id = :lid AND il.case_id = :cid
        """),
        {"lid": lead_id, "cid": case_id},
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found or access denied.")

    expl = row.explanation
    if isinstance(expl, str):
        try:
            expl = json.loads(expl)
        except Exception:
            expl = None

    return {
        "lead_id": str(lead_id),
        "explanation_status": row.explanation_status,
        "explanation": expl,
        "ml_score": float(row.ai_confidence) if row.ai_confidence is not None else None,
        "feature_vector_version": row.feature_vector_version,
        "lead_text": row.lead_text,
        "note": (
            "explanation is NULL when status is REJECTED or SKIPPED. "
            "Deterministic findings remain valid regardless of explanation status."
        ),
    }


@router.get("/{case_id}/leads/{lead_id}/provenance")
async def get_lead_provenance(
    case_id: UUID,
    lead_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    C3-T08: Full provenance chain: LEAD → ML SCORE → FINDINGS → EVIDENCE IDs.
    Enables a reviewer to answer 'Why did CIVIX generate this lead?'
    """
    lead_res = await session.execute(
        text("""
            SELECT il.lead_id, il.ai_confidence, il.feature_vector_version,
                   il.explanation_status, il.generated_by_run_id,
                   p.display_name AS subject_name,
                   ar.model_name, ar.model_version, ar.started_at
            FROM civix.investigative_lead il
            JOIN civix.person p ON p.entity_id = il.target_entity_id
            LEFT JOIN civix.analysis_run ar ON ar.run_id = il.generated_by_run_id
            WHERE il.lead_id = :lid AND il.case_id = :cid
        """),
        {"lid": lead_id, "cid": case_id},
    )
    lead_row = lead_res.first()
    if not lead_row:
        raise HTTPException(status_code=404, detail="Lead not found or access denied.")

    finding_res = await session.execute(
        text("""
            SELECT finding_id, finding_type, path_description,
                   evidence_ids, key_facts, hop_count, matching_rule_id, suppressed
            FROM civix.investigative_finding
            WHERE lead_id = :lid
            ORDER BY created_at
        """),
        {"lid": lead_id},
    )
    findings_chain = []
    for frow in finding_res.fetchall():
        kf = frow.key_facts
        if isinstance(kf, str):
            try:
                kf = json.loads(kf)
            except Exception:
                kf = [kf]
        findings_chain.append({
            "finding_id": str(frow.finding_id),
            "finding_type": frow.finding_type,
            "path_description": frow.path_description,
            "hop_count": frow.hop_count,
            "matching_rule_id": frow.matching_rule_id,
            "suppressed": frow.suppressed,
            "key_facts": kf or [],
            "evidence_ids": [str(e) for e in (frow.evidence_ids or [])],
        })

    return {
        "lead_id": str(lead_id),
        "subject_name": lead_row.subject_name,
        "provenance_chain": {
            "1_lead": {"lead_id": str(lead_id), "explanation_status": lead_row.explanation_status},
            "2_ml_score": {
                "score": float(lead_row.ai_confidence) if lead_row.ai_confidence is not None else None,
                "model_name": lead_row.model_name,
                "model_version": lead_row.model_version,
                "feature_vector_version": lead_row.feature_vector_version,
                "run_at": lead_row.started_at.isoformat() if lead_row.started_at else None,
            },
            "3_deterministic_findings": findings_chain,
        },
        "provenance_note": (
            "evidence_ids reference civix.assertion or civix.event rows. "
            "Each traces to extraction → observation → evidence_instance → source_record."
        ),
    }


@router.get("/model-metadata", response_model=ModelMetadataResponse)
async def get_model_metadata(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
):
    """C3-T08: XGBoost model metadata. Does not expose weights or thresholds."""
    from civix_api.services.intelligence_engine import FEATURE_VECTOR_VERSION as FVV
    if not MLService.is_loaded():
        raise HTTPException(status_code=503, detail="ML model not loaded.")
    return ModelMetadataResponse(
        model_name="behavioral_xgboost",
        model_version="behavioral_xgboost_20260829T143327",
        feature_count=len(EXPECTED_FEATURES),
        feature_names=EXPECTED_FEATURES,
        feature_vector_version=FVV,
    )
