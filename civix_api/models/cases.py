from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class CaseRegistryItem(BaseModel):
    case_id: UUID
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: str
    status: str
    priority: str
    jurisdiction: str
    police_station: str
    provenance: str = Field(description="GOLDEN or SYNTHETIC")
    source_type: str
    entity_count: int
    evidence_count: int
    event_count: int
    lead_count: int
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

class CaseRegistryPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

class CaseRegistrySummary(BaseModel):
    total_cases: int
    active_cases: int
    critical_cases: int
    golden_cases: int
    synthetic_cases: int
    updated_today: int

class CaseRegistryResponse(BaseModel):
    items: List[CaseRegistryItem]
    pagination: CaseRegistryPagination
    summary: CaseRegistrySummary
