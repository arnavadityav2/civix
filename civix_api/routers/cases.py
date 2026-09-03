from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class CaseEntityRoleEnum(str, Enum):
    SUSPECT = 'SUSPECT'
    VICTIM = 'VICTIM'
    COMPLAINANT = 'COMPLAINANT'
    WITNESS = 'WITNESS'
    PERSON_OF_INTEREST = 'PERSON_OF_INTEREST'
    ACCUSED = 'ACCUSED'
    ACQUITTED = 'ACQUITTED'
    OFFICER_IN_CHARGE = 'OFFICER_IN_CHARGE'
    INFORMANT = 'INFORMANT'
    SUBJECT_ORG = 'SUBJECT_ORG'
    SUBJECT_VEHICLE = 'SUBJECT_VEHICLE'
    SUBJECT_ACCOUNT = 'SUBJECT_ACCOUNT'
    SUBJECT_PROPERTY = 'SUBJECT_PROPERTY'
    SUBJECT_DEVICE = 'SUBJECT_DEVICE'
    RELATED_PERSON = 'RELATED_PERSON'
from sqlalchemy.exc import IntegrityError
import json

from civix_api.dependencies import get_current_user_from_token, get_rls_session, get_neo4j_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.services.neo4j_query import Neo4jQueryService
from civix_api.models.graph import GraphResponse
from neo4j import AsyncSession as Neo4jAsyncSession

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["cases"]
)

async def resolve_case_id(session: AsyncSession, case_id_or_num: str) -> UUID:
    try:
        case_uuid = UUID(case_id_or_num)
        # RLS ensures we only see the case if we have access
        result = await session.execute(
            text("SELECT case_id FROM civix.investigative_case WHERE case_id = :cid"),
            {"cid": case_uuid}
        )
    except ValueError:
        # Not a UUID, try case_number
        result = await session.execute(
            text("SELECT case_id FROM civix.investigative_case WHERE case_number = :num"),
            {"num": case_id_or_num}
        )
    
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
    return row[0]


class CaseCreateRequest(BaseModel):
    case_number: str
    title: str
    case_type: str
    jurisdiction: str
    priority: str = "MEDIUM"
    investigating_unit: Optional[str] = None

class CaseEntityRoleRequest(BaseModel):
    entity_id: UUID
    role: CaseEntityRoleEnum
    role_basis: Optional[str] = None

class CaseEntityRoleResponse(BaseModel):
    role_id: UUID
    case_id: UUID
    entity_id: UUID
    role: CaseEntityRoleEnum
    role_basis: Optional[str]
    assigned_by: Optional[UUID]
    valid_from: Optional[Any]
    valid_to: Optional[Any]

@router.post("")
async def create_case(
    case_data: CaseCreateRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    case_id = uuid4()
    access_id = uuid4()

    # 1. Insert case_access FIRST
    await session.execute(
        text("""
            INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
            VALUES (:aid, :cid, :uid, 'ADMIN', :uid)
        """),
        {
            "aid": access_id,
            "cid": case_id,
            "uid": user.user_id
        }
    )

    # 2. Insert investigative_case SECOND
    await session.execute(
        text("""
            INSERT INTO civix.investigative_case (
                case_id, case_number, title, case_type, priority, jurisdiction, 
                investigating_unit, opened_at, lead_investigator_id
            )
            VALUES (
                :cid, :num, :title, :type, :prio, :jur, :unit, now(), :uid
            )
        """),
        {
            "cid": case_id,
            "num": case_data.case_number,
            "title": case_data.title,
            "type": case_data.case_type,
            "prio": case_data.priority,
            "jur": case_data.jurisdiction,
            "unit": case_data.investigating_unit,
            "uid": user.user_id
        }
    )

    # Note: commit happens automatically in the dependency generator, 
    # but we can return the case details directly.
    return {
        "case_id": str(case_id),
        "case_number": case_data.case_number,
        "title": case_data.title,
        "status": "OPEN"
    }

@router.get("")
async def list_cases(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> List[Dict[str, Any]]:
    # RLS enforces visibility automatically
    result = await session.execute(
        text("""
            SELECT case_id, case_number, title, case_type, status, priority, jurisdiction
            FROM civix.investigative_case
            ORDER BY created_at DESC
        """)
    )
    cases = []
    for row in result.fetchall():
        cases.append({
            "case_id": str(row[0]),
            "case_number": row[1],
            "title": row[2],
            "case_type": row[3],
            "status": row[4],
            "priority": row[5],
            "jurisdiction": row[6]
        })
    return cases

@router.get("/{case_id}")
async def get_case(
    case_id: str,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    real_case_id = await resolve_case_id(session, case_id)
    
    # RLS enforces visibility automatically
    result = await session.execute(
        text("""
            SELECT case_id, case_number, title, case_type, status, priority, jurisdiction
            FROM civix.investigative_case
            WHERE case_id = :cid
        """),
        {"cid": real_case_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
    return {
        "case_id": str(row[0]),
        "case_number": row[1],
        "title": row[2],
        "case_type": row[3],
        "status": row[4],
        "priority": row[5],
        "jurisdiction": row[6]
    }

@router.post("/{case_id}/entities", response_model=CaseEntityRoleResponse, status_code=status.HTTP_201_CREATED)
async def link_entity_to_case(
    case_id: str,
    request: CaseEntityRoleRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    real_case_id = await resolve_case_id(session, case_id)

    # 1. Authorization: check if user is ADMIN globally OR has WRITE/ADMIN on this case
    if user.role not in ("ADMIN", "SUPERVISOR"):
        auth_result = await session.execute(
            text("""
                SELECT permission_level FROM civix.case_access 
                WHERE case_id = :cid AND user_id = :uid AND is_revoked = FALSE
                  AND (valid_until IS NULL OR valid_until > now())
            """), 
            {"cid": real_case_id, "uid": user.user_id}
        )
        auth = auth_result.first()
        if not auth or auth[0] not in ('WRITE', 'ADMIN'):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission to modify case")

    # 2. Check if case exists (already checked by resolve_case_id, but keeping for logic flow)
    case_check = await session.execute(
        text("SELECT 1 FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": real_case_id}
    )
    if not case_check.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # 3. Check if entity exists
    entity_check = await session.execute(
        text("SELECT 1 FROM civix.entity WHERE entity_id = :eid"), 
        {"eid": request.entity_id}
    )
    if not entity_check.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entity not found")

    # 4. Insert into case_entity_role
    role_id = uuid4()
    try:
        await session.execute(text("""
            INSERT INTO civix.case_entity_role (
                role_id, case_id, entity_id, role, role_basis, assigned_by
            )
            VALUES (
                :rid, :cid, :eid, CAST(:role AS civix.case_entity_role_enum), :basis, :uid
            )
        """), {
            "rid": role_id,
            "cid": real_case_id,
            "eid": request.entity_id,
            "role": request.role,
            "basis": request.role_basis,
            "uid": user.user_id
        })
        
        # 5. Fetch back the inserted record to return exactly what the database has
        result = await session.execute(text("""
            SELECT role_id, case_id, entity_id, role, role_basis, assigned_by, valid_from, valid_to
            FROM civix.case_entity_role
            WHERE role_id = :rid
        """), {"rid": role_id})
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve inserted role")
            
        # 6. Insert Audit Event
        metadata = {
            "entity_id": str(request.entity_id),
            "role": request.role,
            "role_basis": request.role_basis
        }
        await session.execute(text("""
            INSERT INTO civix.audit_event (
                user_id, action, target_table, target_id, case_context_id, metadata
            ) VALUES (
                :uid, 'WRITE', 'case_entity_role', :rid, :cid, :meta
            )
        """), {
            "uid": user.user_id,
            "rid": role_id,
            "cid": real_case_id,
            "meta": json.dumps(metadata)
        })
        
        return {
            "role_id": row[0],
            "case_id": row[1],
            "entity_id": row[2],
            "role": row[3],
            "role_basis": row[4],
            "assigned_by": row[5],
            "valid_from": row[6],
            "valid_to": row[7]
        }
        
    except IntegrityError as e:
        # 6. Handle duplicate assignment
        if "uq_active_case_entity_role" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Entity is already actively linked to this case with the specified role."
            )
        # Catch invalid enum mapping error
        if "invalid input value for enum" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role enum value: {request.role}"
            )
        raise

@router.get("/{case_id}/graph", response_model=GraphResponse)
async def get_case_graph(
    case_id: str,
    depth: int = Query(1, ge=0, le=2, description="Traversal depth (max 2)"),
    node_limit: int = Query(100, ge=1, le=500, description="Max nodes to return"),
    rel_limit: int = Query(200, ge=1, le=1000, description="Max relationships to return"),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    pg_session: AsyncSession = Depends(get_rls_session),
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session)
):
    real_case_id = await resolve_case_id(pg_session, case_id)

    # 1. Verify root case authorization through PostgreSQL RLS
    # (Already performed during resolve_case_id, but doing it again to be strictly aligned with existing logic)
    verify_result = await pg_session.execute(
        text("SELECT 1 FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": real_case_id}
    )
    if not verify_result.first():
        # User does not have access or case doesn't exist
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # 2. Fetch full ACL (all accessible case_ids) for the user
    # Note: civic.get_accessible_case_ids() returns an array, but we can also just query it via RLS
    acl_result = await pg_session.execute(
        text("SELECT case_id FROM civix.investigative_case")
    )
    accessible_case_ids = [str(row[0]) for row in acl_result.fetchall()]

    # 3. Query Neo4j, passing the ACL as a parameter to strictly limit protected nodes
    graph = await Neo4jQueryService.get_case_graph(
        session=neo4j_session,
        case_id=str(real_case_id),
        accessible_case_ids=accessible_case_ids,
        depth=depth,
        node_limit=node_limit,
        rel_limit=rel_limit
    )
    return graph
