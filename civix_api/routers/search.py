from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.models.search import SearchResponse, SearchResult

router = APIRouter(
    prefix="/api/v1",
    tags=["search"]
)

@router.get("/search", response_model=SearchResponse)
async def search_entities(
    q: str = Query(..., min_length=3),
    entity_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Search for entities globally with strict case isolation.
    """
    q_exact = q
    q_like = f"%{q}%"

    query_str = """
    WITH search_candidates AS (
        SELECT entity_id, 'PERSON' AS entity_type, display_name AS display_label, 'display_name' AS matched_field
        FROM civix.person WHERE display_name ILIKE :q_like
        UNION ALL
        SELECT entity_id, 'ORGANIZATION', legal_name, 'legal_name'
        FROM civix.organization WHERE legal_name ILIKE :q_like
        UNION ALL
        SELECT entity_id, 'DEVICE', imei, 'imei'
        FROM civix.device WHERE imei = :q_exact
        UNION ALL
        SELECT entity_id, 'DEVICE', mac_address, 'mac_address'
        FROM civix.device WHERE mac_address = :q_exact
        UNION ALL
        SELECT entity_id, 'PHONE_NUMBER', msisdn, 'msisdn'
        FROM civix.phone_number WHERE msisdn = :q_exact
        UNION ALL
        SELECT entity_id, 'VEHICLE', registration_number, 'registration_number'
        FROM civix.vehicle WHERE registration_number = :q_exact
        UNION ALL
        SELECT entity_id, 'SOURCE_IDENTITY', raw_identifier, 'raw_identifier'
        FROM civix.source_identity WHERE raw_identifier = :q_exact
        UNION ALL
        SELECT entity_id, 'FINANCIAL_ACCOUNT', masked_number, 'masked_number'
        FROM civix.financial_account WHERE masked_number = :q_exact
    )
    SELECT DISTINCT ON (sc.entity_id)
           sc.entity_id, sc.entity_type, sc.display_label, sc.matched_field
    FROM search_candidates sc
    JOIN civix.entity e ON e.entity_id = sc.entity_id
    WHERE e.visibility_status = 'ACTIVE'
    """
    
    if entity_type:
        query_str += " AND e.entity_type = :entity_type "

    query_str += """
      AND EXISTS (
          SELECT 1 
          FROM civix.case_entity_role cer
          JOIN civix.case_access ca ON cer.case_id = ca.case_id
          WHERE cer.entity_id = e.entity_id
            AND ca.user_id = current_setting('civix.current_user_id', true)::UUID
            AND ca.is_revoked = FALSE
            AND ca.permission_level IN ('READ', 'WRITE', 'ADMIN')
      )
    ORDER BY sc.entity_id
    LIMIT :limit OFFSET :offset
    """

    params = {
        "q_like": q_like,
        "q_exact": q_exact,
        "limit": limit,
        "offset": offset
    }
    
    if entity_type:
        params["entity_type"] = entity_type

    result = await session.execute(text(query_str), params)
    
    results = []
    for row in result.fetchall():
        results.append(SearchResult(
            entity_id=row.entity_id,
            entity_type=row.entity_type,
            display_label=row.display_label,
            matched_field=row.matched_field
        ))
        
    return SearchResponse(
        results=results,
        limit=limit,
        offset=offset
    )
