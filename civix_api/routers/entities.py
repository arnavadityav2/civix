from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
from uuid import UUID

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.models.entity import (
    EntityResponse, EntityBase, PersonData, DeviceData, 
    OrganizationData, PhoneNumberData, SourceIdentityData
)

router = APIRouter(
    prefix="/api/v1/entities",
    tags=["entities"]
)

@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    # Base query with existence and authorization check
    # Visibility logic: entity must be ACTIVE, and there must exist a role linking it to a case 
    # where the user has READ, WRITE, or ADMIN access.
    base_query = text("""
        SELECT e.entity_id, e.entity_type, e.created_at, e.visibility_status
        FROM civix.entity e
        WHERE e.entity_id = :eid
          AND e.visibility_status = 'ACTIVE'
          AND EXISTS (
              SELECT 1 
              FROM civix.case_entity_role cer
              JOIN civix.case_access ca ON cer.case_id = ca.case_id
              WHERE cer.entity_id = e.entity_id
                AND ca.user_id = :uid
                AND ca.is_revoked = FALSE
                AND ca.permission_level IN ('READ', 'WRITE', 'ADMIN')
          )
    """)
    
    result = await session.execute(base_query, {"eid": entity_id, "uid": user.user_id})
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
        
    entity_base = EntityBase.model_validate(row)
    
    entity_type_str = row.entity_type.upper()
    subtype_data_dict = {}
    
    if entity_type_str == 'PERSON':
        st_res = await session.execute(text("SELECT * FROM civix.person WHERE entity_id = :eid"), {"eid": entity_id})
        st_row = st_res.first()
        if st_row:
            subtype_data_dict = PersonData.model_validate(st_row).model_dump()
            
    elif entity_type_str == 'DEVICE':
        st_res = await session.execute(text("SELECT * FROM civix.device WHERE entity_id = :eid"), {"eid": entity_id})
        st_row = st_res.first()
        if st_row:
            subtype_data_dict = DeviceData.model_validate(st_row).model_dump()
            
    elif entity_type_str == 'ORGANIZATION':
        st_res = await session.execute(text("SELECT * FROM civix.organization WHERE entity_id = :eid"), {"eid": entity_id})
        st_row = st_res.first()
        if st_row:
            subtype_data_dict = OrganizationData.model_validate(st_row).model_dump()
            
    elif entity_type_str == 'PHONE_NUMBER':
        st_res = await session.execute(text("SELECT * FROM civix.phone_number WHERE entity_id = :eid"), {"eid": entity_id})
        st_row = st_res.first()
        if st_row:
            subtype_data_dict = PhoneNumberData.model_validate(st_row).model_dump()
            
    elif entity_type_str == 'SOURCE_IDENTITY':
        st_res = await session.execute(text("SELECT * FROM civix.source_identity WHERE entity_id = :eid"), {"eid": entity_id})
        st_row = st_res.first()
        if st_row:
            subtype_data_dict = SourceIdentityData.model_validate(st_row).model_dump()
            
    # Identity Resolution logic is explicitly excluded from Entity Retrieval by ADR-033.
            
    return EntityResponse(
        entity=entity_base,
        subtype_data=subtype_data_dict
    )
