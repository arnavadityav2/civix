
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from uuid import UUID

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.models.ingest import CDRIngestRequest, TransactionIngestRequest, IngestResponse

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["ingest"]
)

async def check_case_write_access(session: AsyncSession, case_id: UUID, user_id: UUID):
    result = await session.execute(
        text("""
            SELECT permission_level 
            FROM civix.case_access 
            WHERE case_id = :cid AND user_id = :uid AND is_revoked = false
        """),
        {"cid": case_id, "uid": user_id}
    )
    access_row = result.first()
    if not access_row or access_row.permission_level not in ('WRITE', 'ADMIN'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: Requires WRITE or ADMIN access to the case."
        )

@router.post("/{case_id}/ingest/cdr", response_model=IngestResponse)
async def ingest_cdr(
    case_id: UUID,
    req: CDRIngestRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    await check_case_write_access(session, case_id, user.user_id)
    
    # 1. Verify source exists
    res = await session.execute(
        text("SELECT source_id FROM civix.source WHERE source_id = :sid"),
        {"sid": req.source_id}
    )
    if not res.first():
        raise HTTPException(status_code=422, detail="Invalid source_id")

    accepted_count = 0
    duplicate_count = 0
    
    if not req.records:
        return IngestResponse(accepted_count=0, duplicate_count=0, status="SUCCESS")

    # 3. Create Artifact for the batch
    batch_json = req.model_dump_json()
    batch_bytes = batch_json.encode('utf-8')
    batch_hash = hashlib.sha256(batch_bytes).digest()
    
    art_res = await session.execute(
        text("""
            INSERT INTO civix.evidence_artifact (sha256_hash, hash_algorithm, file_size_bytes, mime_type, original_filename)
            VALUES (:hash, 'SHA256', :size, 'application/json', 'cdr_batch.json')
            ON CONFLICT (sha256_hash, hash_algorithm) DO NOTHING
            RETURNING artifact_id
        """),
        {"hash": batch_hash, "size": len(batch_bytes)}
    )
    artifact_id = art_res.scalar()
    
    if not artifact_id:
        art_res = await session.execute(
            text("SELECT artifact_id FROM civix.evidence_artifact WHERE sha256_hash = :hash AND hash_algorithm = 'SHA256'"),
            {"hash": batch_hash}
        )
        artifact_id = art_res.scalar()

    # 4. Insert new source records & evidence instances & source identities
    for r in req.records:
        raw_hash = hashlib.sha256(r.model_dump_json().encode('utf-8')).digest()
        sr_res = await session.execute(
            text("""
                INSERT INTO civix.source_record (source_id, external_reference, record_type, raw_content_hash)
                VALUES (:sid, :ext_ref, 'CDR_ROW', :rhash)
                ON CONFLICT (source_id, COALESCE(external_reference, ENCODE(raw_content_hash, 'hex'))) DO NOTHING
                RETURNING source_record_id
            """),
            {"sid": req.source_id, "ext_ref": r.external_reference, "rhash": raw_hash}
        )
        source_record_id = sr_res.scalar()
        
        if not source_record_id:
            duplicate_count += 1
            continue
            
        accepted_count += 1
        
        # Link to case via evidence_instance
        await session.execute(
            text("""
                INSERT INTO civix.evidence_instance (artifact_id, case_id, source_record_id, acquired_by, acquisition_method)
                VALUES (:aid, :cid, :srid, :uid, 'API_INGESTION')
            """),
            {"aid": artifact_id, "cid": case_id, "srid": source_record_id, "uid": user.user_id}
        )
        
        # Insert Caller source_identity
        await session.execute(
            text("""
                WITH new_entity AS (
                    INSERT INTO civix.entity (entity_type) VALUES ('SOURCE_IDENTITY') RETURNING entity_id
                )
                INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, source_record_id, observed_at)
                SELECT entity_id, :raw_id, 'PHONE_MSISDN', :srid, :obs
                FROM new_entity
            """),
            {"raw_id": r.caller_identifier, "srid": source_record_id, "obs": r.timestamp}
        )
        
        # Insert Callee source_identity
        await session.execute(
            text("""
                WITH new_entity AS (
                    INSERT INTO civix.entity (entity_type) VALUES ('SOURCE_IDENTITY') RETURNING entity_id
                )
                INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, source_record_id, observed_at)
                SELECT entity_id, :raw_id, 'PHONE_MSISDN', :srid, :obs
                FROM new_entity
            """),
            {"raw_id": r.callee_identifier, "srid": source_record_id, "obs": r.timestamp}
        )

    await session.commit()
    
    return IngestResponse(
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        status="SUCCESS"
    )

@router.post("/{case_id}/ingest/transaction", response_model=IngestResponse)
async def ingest_transaction(
    case_id: UUID,
    req: TransactionIngestRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    await check_case_write_access(session, case_id, user.user_id)
    
    # 1. Verify source exists
    res = await session.execute(
        text("SELECT source_id FROM civix.source WHERE source_id = :sid"),
        {"sid": req.source_id}
    )
    if not res.first():
        raise HTTPException(status_code=422, detail="Invalid source_id")

    accepted_count = 0
    duplicate_count = 0
    
    if not req.records:
        return IngestResponse(accepted_count=0, duplicate_count=0, status="SUCCESS")

    # 3. Create Artifact for the batch
    batch_json = req.model_dump_json()
    batch_bytes = batch_json.encode('utf-8')
    batch_hash = hashlib.sha256(batch_bytes).digest()
    
    art_res = await session.execute(
        text("""
            INSERT INTO civix.evidence_artifact (sha256_hash, hash_algorithm, file_size_bytes, mime_type, original_filename)
            VALUES (:hash, 'SHA256', :size, 'application/json', 'transaction_batch.json')
            ON CONFLICT (sha256_hash, hash_algorithm) DO NOTHING
            RETURNING artifact_id
        """),
        {"hash": batch_hash, "size": len(batch_bytes)}
    )
    artifact_id = art_res.scalar()
    
    if not artifact_id:
        art_res = await session.execute(
            text("SELECT artifact_id FROM civix.evidence_artifact WHERE sha256_hash = :hash AND hash_algorithm = 'SHA256'"),
            {"hash": batch_hash}
        )
        artifact_id = art_res.scalar()

    # 4. Insert new source records & evidence instances & source identities
    for r in req.records:
        raw_hash = hashlib.sha256(r.model_dump_json().encode('utf-8')).digest()
        sr_res = await session.execute(
            text("""
                INSERT INTO civix.source_record (source_id, external_reference, record_type, raw_content_hash)
                VALUES (:sid, :ext_ref, 'TRANSACTION_ROW', :rhash)
                ON CONFLICT (source_id, COALESCE(external_reference, ENCODE(raw_content_hash, 'hex'))) DO NOTHING
                RETURNING source_record_id
            """),
            {"sid": req.source_id, "ext_ref": r.external_reference, "rhash": raw_hash}
        )
        source_record_id = sr_res.scalar()
        
        if not source_record_id:
            duplicate_count += 1
            continue
            
        accepted_count += 1
        
        # Link to case via evidence_instance
        await session.execute(
            text("""
                INSERT INTO civix.evidence_instance (artifact_id, case_id, source_record_id, acquired_by, acquisition_method)
                VALUES (:aid, :cid, :srid, :uid, 'API_INGESTION')
            """),
            {"aid": artifact_id, "cid": case_id, "srid": source_record_id, "uid": user.user_id}
        )
        
        # Insert Source Account source_identity
        await session.execute(
            text("""
                WITH new_entity AS (
                    INSERT INTO civix.entity (entity_type) VALUES ('SOURCE_IDENTITY') RETURNING entity_id
                )
                INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, source_record_id, observed_at)
                SELECT entity_id, :raw_id, 'OTHER', :srid, :obs
                FROM new_entity
            """),
            {"raw_id": r.source_account, "srid": source_record_id, "obs": r.timestamp}
        )
        
        # Insert Destination Account source_identity
        await session.execute(
            text("""
                WITH new_entity AS (
                    INSERT INTO civix.entity (entity_type) VALUES ('SOURCE_IDENTITY') RETURNING entity_id
                )
                INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, source_record_id, observed_at)
                SELECT entity_id, :raw_id, 'OTHER', :srid, :obs
                FROM new_entity
            """),
            {"raw_id": r.destination_account, "srid": source_record_id, "obs": r.timestamp}
        )

    await session.commit()
    
    return IngestResponse(
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        status="SUCCESS"
    )
