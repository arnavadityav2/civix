from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conlist, model_validator
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class CDRRecord(BaseModel):
    external_reference: Optional[str] = Field(default=None, description="Unique reference from the source provider")
    caller_identifier: str = Field(..., description="Caller's identifier (e.g. MSISDN)")
    callee_identifier: str = Field(..., description="Callee's identifier (e.g. MSISDN)")
    timestamp: datetime
    duration_seconds: Optional[int] = None
    location_metadata: Optional[Dict[str, Any]] = None
    raw_metadata: Optional[Dict[str, Any]] = None

class CDRIngestRequest(BaseModel):
    source_id: UUID
    records: List[CDRRecord] = Field(..., max_length=500, min_length=1)

class TransactionRecord(BaseModel):
    external_reference: Optional[str] = Field(default=None, description="Unique reference from the source provider")
    source_account: str
    destination_account: str
    amount: Decimal
    currency: str = Field(default="INR")
    timestamp: datetime
    transaction_type: str
    raw_metadata: Optional[Dict[str, Any]] = None


class TransactionIngestRequest(BaseModel):
    source_id: UUID
    records: List[TransactionRecord] = Field(..., max_length=500, min_length=1)

class IngestResponse(BaseModel):
    accepted_count: int
    duplicate_count: int
    status: str
