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
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/biometric",
    tags=["Biometric Intelligence"],
)

# Engine loading is handled by lifespan in main.py.
# This module-level call ensures the engine is ready if the router is
# used in isolation or tested directly.
def _try_preload_engine():
    try:
        biometric_engine.load()
    except Exception as e:
        logger.warning(f"Biometric engine could not preload at import time: {e}")

_try_preload_engine()


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
            # NOTE: avatar_url does NOT exist in civix.person schema — omitted intentionally.
            r = await db.execute(
                text("SELECT display_name, gender, date_of_birth, nationality FROM civix.person WHERE entity_id = :pid"),
                {"pid": person_id}
            )
            person = r.fetchone()
            
            if person:
                result["person_name"] = person[0]
                result["avatar_url"] = None  # avatar_url not in current schema
                
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


@router.get("/availability/{person_id}")
async def check_biometric_availability(
    person_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Check whether a person has biometric enrollment in the CIVIX index.
    Used by the frontend to dynamically determine if [ANALYZE] or [NO REFERENCE] should be shown.
    Returns enrollment status and reference count without exposing the raw embeddings.
    """
    try:
        if not biometric_engine._is_loaded:
            biometric_engine.load()
        refs = biometric_engine.get_reference_info(person_id)
        return {
            "person_id": person_id,
            "enrolled": len(refs) > 0,
            "reference_count": len(refs),
            "index_source": biometric_engine.index.get("source", "UNKNOWN") if biometric_engine._is_loaded else "UNKNOWN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-availability")
async def batch_biometric_availability(
    person_ids: List[str],
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Batch availability check for multiple person_ids at once.
    Used by the Case → Biometric Manifest endpoint to determine
    which persons in a case have biometric enrollment.
    """
    try:
        if not biometric_engine._is_loaded:
            biometric_engine.load()
        result = {}
        for pid in person_ids:
            refs = biometric_engine.get_reference_info(pid)
            result[pid] = {
                "enrolled": len(refs) > 0,
                "reference_count": len(refs)
            }
        return {"availability": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/cctv-trace/{person_id}")
async def get_cctv_trace(
    person_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve CCTV observations associated with a person via their case linkage.
    Returns camera-level observations with timestamps, locations, and signal class.
    
    NOTE: The `cctv_observation` table records investigator-reviewed observations.
    These are currently empty in the live demo environment. This endpoint returns
    an empty-but-valid response when no observations exist.
    
    Architecture note: cctv_observation currently links to vehicles, not persons directly.
    Future extension: Add person_id FK to cctv_observation for direct person-level CCTV trace.
    """
    try:
        # Get cases linked to this person
        r_cases = await db.execute(
            text("""
                SELECT DISTINCT cer.case_id
                FROM civix.case_entity_role cer
                WHERE cer.entity_id = :pid
            """),
            {"pid": person_id}
        )
        case_ids = [str(row[0]) for row in r_cases.fetchall()]

        observations = []
        if case_ids:
            # Query cctv_observations linked to those cases
            r_obs = await db.execute(
                text("""
                    SELECT 
                        co.observation_id,
                        co.case_id,
                        co.camera_id,
                        co.signal_class,
                        co.reviewed_at,
                        co.investigator_notes,
                        cam.camera_code,
                        cam.display_name as camera_name,
                        cam.city,
                        cam.region,
                        cam.latitude,
                        cam.longitude
                    FROM civix.cctv_observation co
                    LEFT JOIN civix.cctv_camera cam ON co.camera_id = cam.camera_id
                    WHERE co.case_id = ANY(:case_ids)
                    ORDER BY co.reviewed_at ASC
                    LIMIT 50
                """),
                {"case_ids": case_ids}
            )
            for row in r_obs.fetchall():
                m = row._mapping
                observations.append({
                    "observation_id": str(m["observation_id"]),
                    "case_id": str(m["case_id"]),
                    "camera_id": str(m["camera_id"]) if m["camera_id"] else None,
                    "signal_class": m["signal_class"],
                    "timestamp": m["reviewed_at"].isoformat() if m["reviewed_at"] else None,
                    "investigator_notes": m["investigator_notes"],
                    "camera_code": m["camera_code"],
                    "camera_name": m["camera_name"],
                    "city": m["city"],
                    "region": m["region"],
                    "latitude": float(m["latitude"]) if m["latitude"] is not None else None,
                    "longitude": float(m["longitude"]) if m["longitude"] is not None else None,
                })

        return {
            "person_id": person_id,
            "observations": observations,
            "observation_count": len(observations),
            "data_source": "CIVIX_CCTV_OBSERVATION_TABLE",
            "note": "SYNTHETIC_DEMO" if not observations else "LIVE_DATA"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CCTV trace retrieval failed: {str(e)}"
        )


@router.get("/person-summary/{person_id}")
async def get_person_summary(
    person_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Return basic person details for display in the biometric workstation.
    Combines data from civix.person and civix.entity.
    """
    try:
        r = await db.execute(
            text("""
                SELECT p.display_name, p.gender, p.date_of_birth, p.nationality,
                       p.is_deceased, p.notes, e.entity_type::text, e.visibility_status::text
                FROM civix.person p
                JOIN civix.entity e ON p.entity_id = e.entity_id
                WHERE p.entity_id = :pid
            """),
            {"pid": person_id}
        )
        row = r.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Person not found")

        m = row._mapping
        return {
            "person_id": person_id,
            "display_name": m["display_name"],
            "gender": m["gender"],
            "date_of_birth": m["date_of_birth"].isoformat() if m["date_of_birth"] else None,
            "nationality": m["nationality"],
            "is_deceased": m["is_deceased"],
            "notes": m["notes"],
            "entity_type": m["entity_type"],
            "visibility_status": m["visibility_status"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Person summary retrieval failed: {str(e)}"
        )
