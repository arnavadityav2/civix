"""
CIVIX 2.0 — Evidence Router
Round 2A

Endpoints:
  POST   /api/v1/cases/{case_id}/evidence/upload
         Upload a document/image as evidence. Returns 202 immediately.
         Background task handles text extraction + NLP.

  POST   /api/v1/cases/{case_id}/evidence/{artifact_id}/process
         Trigger/retry processing for an already-uploaded artifact.

  GET    /api/v1/cases/{case_id}/evidence
         List all evidence for a case (RLS enforced).

  GET    /api/v1/cases/{case_id}/evidence/{artifact_id}
         Get detailed status for a specific evidence artifact.
"""
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, BackgroundTasks, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.models.evidence import (
    EvidenceUploadResponse, EvidenceStatusResponse,
    EvidenceListItem, ProcessTriggerResponse
)
from civix_api.services import evidence_store
from civix_api.services.evidence_pipeline import run_evidence_pipeline, ensure_nlp_source_exists

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["evidence"]
)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


async def _check_case_write_access(session: AsyncSession, case_id: UUID, user_id: UUID):
    result = await session.execute(
        text("""
            SELECT permission_level
            FROM civix.case_access
            WHERE case_id = :cid AND user_id = :uid AND is_revoked = false
        """),
        {"cid": case_id, "uid": user_id}
    )
    row = result.first()
    if not row or row.permission_level not in ("WRITE", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Requires WRITE or ADMIN access to the case."
        )


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/evidence/upload
# ---------------------------------------------------------------------------
@router.post(
    "/{case_id}/evidence/upload",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload evidence file for a case"
)
async def upload_evidence(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Evidence file to upload"),
    acquisition_method: str = Form(default="FIELD_COLLECTION"),
    acquisition_context: str = Form(default=""),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    # 1. Authorization
    await _check_case_write_access(session, case_id, user.user_id)

    # 2. Case exists check (RLS auto-enforces)
    case_check = await session.execute(
        text("SELECT case_id, title, case_type, jurisdiction FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": case_id}
    )
    case_row = case_check.first()
    if not case_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    case_context = f"{case_row.case_type} investigation, {case_row.jurisdiction}"

    # 3. Read file bytes
    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file rejected.")

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.1f}MB exceeds maximum of {MAX_UPLOAD_BYTES // (1024 * 1024)}MB."
        )

    # 4. Compute SHA-256 and store to filesystem
    original_filename = file.filename or "evidence_file"
    storage_uri, sha256_hex, is_duplicate_on_disk = evidence_store.store_file(
        file_bytes, original_filename
    )

    # Detect MIME from content (not from client)
    from civix_api.services.processors.resolver import detect_mime_type
    detected_mime = detect_mime_type(file_bytes, original_filename)

    sha256_raw = bytes.fromhex(sha256_hex)

    # 5. Insert or retrieve evidence_artifact (idempotent via ON CONFLICT)
    art_res = await session.execute(text("""
        INSERT INTO civix.evidence_artifact (
            artifact_id, sha256_hash, hash_algorithm, file_size_bytes,
            mime_type, original_filename, storage_uri,
            is_integrity_verified, processing_status
        )
        VALUES (
            :aid, :hash, 'SHA256', :size,
            :mime, :fname, :uri,
            true, 'STORED'
        )
        ON CONFLICT (sha256_hash, hash_algorithm) DO NOTHING
        RETURNING artifact_id
    """), {
        "aid": uuid4(),
        "hash": sha256_raw,
        "size": len(file_bytes),
        "mime": detected_mime,
        "fname": evidence_store.sanitize_filename(original_filename),
        "uri": storage_uri,
    })
    artifact_id = art_res.scalar()

    is_duplicate_in_db = artifact_id is None
    if is_duplicate_in_db:
        # Artifact already exists — fetch its ID
        fetch_res = await session.execute(text("""
            SELECT artifact_id FROM civix.evidence_artifact
            WHERE sha256_hash = :hash AND hash_algorithm = 'SHA256'
        """), {"hash": sha256_raw})
        artifact_id = fetch_res.scalar()

    # 6. Check if this file is already an evidence_instance for this case
    existing_inst = await session.execute(text("""
        SELECT instance_id FROM civix.evidence_instance
        WHERE artifact_id = :aid AND case_id = :cid AND tx_end IS NULL
    """), {"aid": artifact_id, "cid": case_id})
    existing_row = existing_inst.first()

    if existing_row:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This file (sha256={sha256_hex[:16]}...) has already been ingested for this case."
        )

    # 7. Create evidence_instance (case-scoped reference)
    instance_id = uuid4()
    await session.execute(text("""
        INSERT INTO civix.evidence_instance (
            instance_id, artifact_id, case_id,
            acquired_by, acquisition_method, acquisition_context,
            legal_status, tx_start
        ) VALUES (
            :iid, :aid, :cid,
            :uid, :acq_method, :acq_ctx,
            'ACTIVE', :now
        )
    """), {
        "iid": instance_id,
        "aid": artifact_id,
        "cid": case_id,
        "uid": user.user_id,
        "acq_method": acquisition_method or "UPLOAD",
        "acq_ctx": acquisition_context or "",
        "now": datetime.now(timezone.utc),
    })
    await session.commit()

    # 8. Ensure NLP source row exists
    nlp_source_id = await ensure_nlp_source_exists(session)

    # 9. Queue background processing
    background_tasks.add_task(
        run_evidence_pipeline,
        artifact_id=artifact_id,
        instance_id=instance_id,
        case_id=case_id,
        case_context=case_context,
        storage_uri=storage_uri,
        original_filename=original_filename,
        user_id=user.user_id,
        nlp_source_id=nlp_source_id,
    )

    logger.info(
        f"Evidence uploaded: artifact={artifact_id}, instance={instance_id}, "
        f"case={case_id}, size={len(file_bytes)}B, duplicate_in_db={is_duplicate_in_db}"
    )

    return EvidenceUploadResponse(
        artifact_id=artifact_id,
        instance_id=instance_id,
        original_filename=evidence_store.sanitize_filename(original_filename),
        mime_type=detected_mime,
        sha256_hash=sha256_hex,
        file_size_bytes=len(file_bytes),
        processing_status="STORED",
        is_duplicate=is_duplicate_in_db,
        message=(
            "Evidence stored. Background processing started. "
            "Poll GET /evidence/{artifact_id} for status."
        )
    )


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/evidence/{artifact_id}/process
# ---------------------------------------------------------------------------
@router.post(
    "/{case_id}/evidence/{artifact_id}/process",
    response_model=ProcessTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger or retry processing for an evidence artifact"
)
async def trigger_evidence_processing(
    case_id: UUID,
    artifact_id: UUID,
    background_tasks: BackgroundTasks,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    await _check_case_write_access(session, case_id, user.user_id)

    # Fetch artifact + instance
    result = await session.execute(text("""
        SELECT ea.artifact_id, ea.storage_uri, ea.original_filename,
               ea.processing_status,
               ei.instance_id,
               ic.case_type, ic.jurisdiction
        FROM civix.evidence_artifact ea
        JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
        JOIN civix.investigative_case ic ON ic.case_id = ei.case_id
        WHERE ea.artifact_id = :aid AND ei.case_id = :cid AND ei.tx_end IS NULL
    """), {"aid": artifact_id, "cid": case_id})
    row = result.first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found for this case.")

    current_status = row.processing_status
    if current_status in ("PROCESSING",):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence is currently being processed. Wait for it to complete."
        )

    case_context = f"{row.case_type} investigation, {row.jurisdiction}"
    nlp_source_id = await ensure_nlp_source_exists(session)

    background_tasks.add_task(
        run_evidence_pipeline,
        artifact_id=artifact_id,
        instance_id=row.instance_id,
        case_id=case_id,
        case_context=case_context,
        storage_uri=row.storage_uri,
        original_filename=row.original_filename or "evidence_file",
        user_id=user.user_id,
        nlp_source_id=nlp_source_id,
    )

    return ProcessTriggerResponse(
        artifact_id=artifact_id,
        processing_status="PROCESSING",
        message="Processing queued. Poll GET /evidence/{artifact_id} for status."
    )


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/evidence
# ---------------------------------------------------------------------------
@router.get(
    "/{case_id}/evidence",
    response_model=List[EvidenceListItem],
    summary="List all evidence for a case"
)
async def list_evidence(
    case_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    result = await session.execute(text("""
        SELECT ea.artifact_id, ei.instance_id,
               ea.original_filename, ea.mime_type, ea.file_size_bytes,
               ea.processing_status, ea.created_at
        FROM civix.evidence_artifact ea
        JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
        WHERE ei.case_id = :cid AND ei.tx_end IS NULL
        ORDER BY ea.created_at DESC
    """), {"cid": case_id})

    items = []
    for row in result.fetchall():
        items.append(EvidenceListItem(
            artifact_id=row.artifact_id,
            instance_id=row.instance_id,
            original_filename=row.original_filename,
            mime_type=row.mime_type,
            file_size_bytes=row.file_size_bytes,
            processing_status=row.processing_status,
            created_at=row.created_at,
        ))
    return items


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/evidence/{artifact_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{case_id}/evidence/{artifact_id}",
    response_model=EvidenceStatusResponse,
    summary="Get status of a specific evidence artifact"
)
async def get_evidence_status(
    case_id: UUID,
    artifact_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    result = await session.execute(text("""
        SELECT ea.artifact_id, ei.instance_id,
               ea.original_filename, ea.mime_type, ea.file_size_bytes,
               ea.processing_status, ea.processed_at, ea.processing_error,
               ea.media_metadata, ea.created_at,
               ei.case_id, ei.acquired_by, ei.acquisition_method
        FROM civix.evidence_artifact ea
        JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
        WHERE ea.artifact_id = :aid AND ei.case_id = :cid AND ei.tx_end IS NULL
    """), {"aid": artifact_id, "cid": case_id})

    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")

    return EvidenceStatusResponse(
        artifact_id=row.artifact_id,
        instance_id=row.instance_id,
        original_filename=row.original_filename,
        mime_type=row.mime_type,
        file_size_bytes=row.file_size_bytes,
        processing_status=row.processing_status,
        processed_at=row.processed_at,
        processing_error=row.processing_error,
        media_metadata=row.media_metadata,
        created_at=row.created_at,
        case_id=row.case_id,
        acquired_by=row.acquired_by,
        acquisition_method=row.acquisition_method,
    )
