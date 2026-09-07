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
    person_count: int = 0
    vehicle_count: int = 0
    phone_count: int = 0
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

class EntityCounts(BaseModel):
    person_count: int = 0
    vehicle_count: int = 0
    phone_count: int = 0
    evidence_count: int = 0
    location_count: int = 0
    organization_count: int = 0
    device_count: int = 0

class CaseEntityItem(BaseModel):
    role_id: str
    entity_id: str
    role: str
    role_basis: Optional[str] = None
    entity_type: str
    display_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    avatar_url: Optional[str] = None

class CaseEntitiesResponse(BaseModel):
    items: List[CaseEntityItem]
    total_count: int
    limit: int
    offset: int
    entity_counts: EntityCounts

