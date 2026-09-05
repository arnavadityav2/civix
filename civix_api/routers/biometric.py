from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from civix_api.dependencies import get_db_session as get_db
from civix_api.dependencies import get_current_user_from_token
from civix_api.auth.principal import AuthenticatedCivixUser as User
from civix_api.services.cv.biometric_engine import biometric_engine
from pathlib import Path
import os

router = APIRouter(
    prefix="/api/v1/biometric",
    tags=["Biometric Intelligence"],
)

@router.on_event("startup")
async def startup_event():
    # Load biometric engine in the background at startup
    try:
        biometric_engine.load()
    except Exception as e:
        print(f"Failed to load biometric engine on startup: {e}")


@router.post("/search")
async def search_biometric(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Search the biometric index using an uploaded face image.
    Does not persist the uploaded image.
    """
    try:
        img_bytes = await file.read()
        
        # 1. Run biometric search
        result = biometric_engine.search(img_bytes)
        
        # 2. Add canonical context if there's a match
        if result.get("status") in ["MATCH_FOUND", "AMBIGUOUS_MATCH"] and result.get("person_id"):
            person_id = result["person_id"]
            
            # Fetch base person details
            r = await db.execute(
                text("SELECT display_name, gender, date_of_birth, nationality, avatar_url FROM civix.person WHERE entity_id = :pid"),
                {"pid": person_id}
            )
            person = r.fetchone()
            
            if person:
                result["person_name"] = person[0]
                result["avatar_url"] = person[4]
                
                # Fetch role context to determine classification
                r = await db.execute(
                    text("""
                        SELECT role::text FROM civix.case_entity_role 
                        WHERE entity_id = :pid
                    """),
                    {"pid": person_id}
                )
                roles = [row[0] for row in r.fetchall()]
                
                # Precedence: Investigative subject over civilian
                inv_roles = {"SUSPECT", "ACCUSED", "PERSON_OF_INTEREST"}
                civ_roles = {"VICTIM", "COMPLAINANT", "WITNESS", "INFORMANT", "RELATED_PERSON"}
                
                person_roles = set(roles)
                if person_roles.intersection(inv_roles):
                    result["classification"] = "INVESTIGATIVE_SUBJECT"
                    # Get primary role
                    for role in ["SUSPECT", "ACCUSED", "PERSON_OF_INTEREST"]:
                        if role in person_roles:
                            result["primary_role"] = role
                            break
                elif person_roles.intersection(civ_roles):
                    result["classification"] = "CIVILIAN"
                    # Get primary role
                    for role in ["VICTIM", "COMPLAINANT", "WITNESS", "INFORMANT", "RELATED_PERSON"]:
                        if role in person_roles:
                            result["primary_role"] = role
                            break
                else:
                    result["classification"] = "UNKNOWN"
                    result["primary_role"] = roles[0] if roles else "UNKNOWN"

        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric search failed: {str(e)}"
        )


@router.get("/references/{person_id}")
async def get_references(
    person_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get all biometric index references for a specific person.
    """
    try:
        refs = biometric_engine.get_reference_info(person_id)
        return {"references": refs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/refs/{person_id}/{filename}")
async def get_reference_image(
    person_id: str, 
    filename: str
):
    """
    Serve a reference image for frontend UI thumbnail display.
    """
    # Prevent path traversal
    safe_person_id = os.path.basename(person_id)
    safe_filename = os.path.basename(filename)
    
    file_path = biometric_engine.data_dir / "refs" / safe_person_id / safe_filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Reference image not found")
        
    return FileResponse(str(file_path))


@router.get("/context/{person_id}")
async def get_canonical_context(
    person_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full investigative context for a person matched via biometrics.
    Uses READ-ONLY queries against the canonical PostgreSQL database.
    """
    try:
        # 1. Linked Cases
        r_cases = await db.execute(
            text("""
                SELECT c.case_id, c.case_number, c.title, c.status, cer.role::text
                FROM civix.investigative_case c
                JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
                WHERE cer.entity_id = :pid
                ORDER BY cer.tx_start DESC
            """),
            {"pid": person_id}
        )
        cases = [dict(row._mapping) for row in r_cases.fetchall()]
        case_ids = [c["case_id"] for c in cases]
        
        # 2. Linked Evidence
        evidence = []
        if case_ids:
            r_ev = await db.execute(
                text("""
                    SELECT e.instance_id, e.case_id, e.acquisition_method as label, e.legal_status, 
                           c.case_number
                    FROM civix.evidence_instance e
                    JOIN civix.investigative_case c ON e.case_id = c.case_id
                    WHERE e.case_id = ANY(:case_ids) AND e.tx_end IS NULL
                    LIMIT 10
                """),
                {"case_ids": case_ids}
            )
            evidence = [dict(row._mapping) for row in r_ev.fetchall()]
            
        # 3. Events involving the person
        r_events = await db.execute(
            text("""
                SELECT e.event_id, e.event_type as title, e.description, e.occurred_at as event_date
                FROM civix.event e
                JOIN civix.event_participant ep ON e.event_id = ep.event_id
                WHERE ep.entity_id = :pid
                ORDER BY e.occurred_at DESC
                LIMIT 10
            """),
            {"pid": person_id}
        )
        events = [dict(row._mapping) for row in r_events.fetchall()]
        
        # 4. Leads related to the cases or target entity
        leads = []
        if case_ids:
            r_leads = await db.execute(
                text("""
                    SELECT l.lead_id, l.case_id, l.lead_text as title, l.status,
                           c.case_number
                    FROM civix.investigative_lead l
                    JOIN civix.investigative_case c ON l.case_id = c.case_id
                    WHERE l.case_id = ANY(:case_ids) OR l.target_entity_id = :pid
                    ORDER BY l.created_at DESC
                    LIMIT 10
                """),
                {"case_ids": case_ids, "pid": person_id}
            )
            leads = [dict(row._mapping) for row in r_leads.fetchall()]

        return {
            "person_id": person_id,
            "cases": cases,
            "evidence": evidence,
            "events": events,
            "leads": leads
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context retrieval failed: {str(e)}"
        )
