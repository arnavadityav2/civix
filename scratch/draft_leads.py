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
    valid_statuses = ["OPEN", "IN_PROGRESS", "CONFIRMED", "FALSE_POSITIVE", "CLOSED", "DEFERRED"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=422, detail="Invalid status")

    # 1. Verify case access (must have WRITE access theoretically, but per existing api we just check if it exists and use RLS, wait docs say "must have WRITE access")
    # Actually, civix.case_access permission_level needs to be checked.
    # Let's check how case_access is checked in civix_api. 
    # Usually `get_rls_session` enforces RLS, but we can do an explicit check.
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
            detail="Lead not found."
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
            generated_by_person=row.generated_by_person, ai_confidence=float(row.ai_confidence) if row.ai_confidence is not None else None,
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
        import json
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
