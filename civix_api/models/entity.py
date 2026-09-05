from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date

class EntityBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    entity_id: UUID
    entity_type: str
    created_at: datetime
    visibility_status: str

class PersonData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    display_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    is_deceased: bool
    deceased_at: Optional[date] = None
    notes: Optional[str] = None
    avatar_url: Optional[str] = None

class DeviceData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    imei: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None

class OrganizationData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    legal_name: str
    org_type: str
    registration_number: Optional[str] = None
    incorporation_date: Optional[date] = None
    jurisdiction: Optional[str] = None

class PhoneNumberData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    msisdn: str
    country_code: str
    operator: Optional[str] = None
    number_type: Optional[str] = None

class SourceIdentityData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    raw_identifier: str
    identifier_type: str
    observed_at: datetime

class EntityResponse(BaseModel):
    entity: EntityBase
    subtype_data: Dict[str, Any]
