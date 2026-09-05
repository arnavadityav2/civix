"""
CIVIX 2.0 — Evidence Pydantic Models
Round 2A

These are the request/response models for the evidence ingestion and
retrieval API. They do not contain business logic.
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


# ---------------------------------------------------------------------------
# Upload Response
# Returned immediately (202) when a file is accepted.
# ---------------------------------------------------------------------------
class EvidenceUploadResponse(BaseModel):
    artifact_id: UUID
    instance_id: UUID
    original_filename: str
    mime_type: str
    sha256_hash: str          # hex string representation
    file_size_bytes: int
    processing_status: str    # STORED
    is_duplicate: bool        # True if artifact already existed (same hash)
    message: str


# ---------------------------------------------------------------------------
# Evidence Status Response
# Returned by GET /evidence/{artifact_id}
# ---------------------------------------------------------------------------
class EvidenceStatusResponse(BaseModel):
    artifact_id: UUID
    instance_id: UUID
    original_filename: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    processing_status: str
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    media_metadata: Optional[Dict[str, Any]]
    case_id: UUID
    acquired_by: Optional[UUID]
    acquisition_method: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Evidence List Item (lightweight)
# ---------------------------------------------------------------------------
class EvidenceListItem(BaseModel):
    artifact_id: UUID
    instance_id: UUID
    original_filename: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    processing_status: str
    created_at: datetime
    evidence_type: Optional[str] = None
    evidence_title: Optional[str] = None


# ---------------------------------------------------------------------------
# Process Trigger Response
# Returned by POST /evidence/{artifact_id}/process
# ---------------------------------------------------------------------------
class ProcessTriggerResponse(BaseModel):
    artifact_id: UUID
    processing_status: str
    message: str
