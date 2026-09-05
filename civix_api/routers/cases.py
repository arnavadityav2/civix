import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


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
from civix_api.models.graph import GraphNode, GraphRelationship, GraphResponse, GraphMetadata

from civix_api.models.cases import (
    CaseRegistryItem,
    CaseRegistryPagination,
    CaseRegistrySummary,
    CaseRegistryResponse
)
from neo4j import AsyncSession as Neo4jAsyncSession
import math

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["cases"]
)

SORT_FIELD_MAP = {
    "last_activity_at": "last_activity_at",
    "priority": "c.priority",
    "case_number": "c.case_number",
    "title": "c.title",
    "status": "c.status",
    "jurisdiction": "c.jurisdiction",
    "created_at": "c.created_at",
    "updated_at": "c.updated_at"
}

@router.get("/registry", response_model=CaseRegistryResponse)
async def get_case_registry(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    case_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    provenance: Optional[str] = None,
    sort_by: str = Query("last_activity_at"),
    sort_order: str = Query("desc"),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> CaseRegistryResponse:
    # 1. Whitelist sorting
    sort_col = SORT_FIELD_MAP.get(sort_by, "last_activity_at")
    order_dir = "DESC" if sort_order.lower() == "desc" else "ASC"
    nulls_dir = "NULLS LAST" if order_dir == "DESC" else "NULLS FIRST"

    # 2. Build filter WHERE clause
    where_conditions = []
    query_params: Dict[str, Any] = {
        "limit": page_size,
        "offset": (page - 1) * page_size
    }

    if search:
        where_conditions.append(
            "(c.title ILIKE :search OR c.case_number ILIKE :search OR c.jurisdiction ILIKE :search OR c.police_station ILIKE :search)"
        )
        query_params["search"] = f"%{search.strip()}%"

    if case_type:
        where_conditions.append("c.case_type = :case_type")
        query_params["case_type"] = case_type.upper()

    if status:
        st_upper = status.upper()
        if st_upper == "ACTIVE":
            where_conditions.append("c.status IN ('ACTIVE', 'OPEN')")
        elif st_upper == "UNRESOLVED":
            where_conditions.append("c.status IN ('OPEN', 'CLOSED_UNSOLVED')")
        else:
            where_conditions.append("c.status = :status")
            query_params["status"] = st_upper

    if priority:
        where_conditions.append("c.priority = :priority")
        query_params["priority"] = priority.upper()

    if jurisdiction:
        where_conditions.append(
            "(c.jurisdiction ILIKE :jurisdiction OR c.police_station ILIKE :jurisdiction)"
        )
        query_params["jurisdiction"] = f"%{jurisdiction.strip()}%"

    if provenance:
        prov_upper = provenance.upper()
        if prov_upper == "GOLDEN":
            where_conditions.append("c.case_number NOT LIKE 'SYN-%'")
        elif prov_upper == "SYNTHETIC":
            where_conditions.append("c.case_number LIKE 'SYN-%'")

    where_sql = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

    # 3. Query items & pagination total
    items_sql = text(f"""
        WITH case_entities AS (
            SELECT case_id, COUNT(DISTINCT entity_id) as entity_count
            FROM civix.case_entity_role
            GROUP BY case_id
        ),
        case_evidence AS (
            SELECT case_id, COUNT(DISTINCT instance_id) as evidence_count
            FROM civix.evidence_instance
            GROUP BY case_id
        ),
        combined_events AS (
            SELECT case_id, event_id FROM civix.event_location WHERE case_id IS NOT NULL
            UNION
            SELECT cer.case_id, ep.event_id 
            FROM civix.event_participant ep 
            JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
        ),
        case_events AS (
            SELECT case_id, COUNT(DISTINCT event_id) as event_count
            FROM combined_events
            GROUP BY case_id
        ),
        case_leads AS (
            SELECT case_id, COUNT(DISTINCT lead_id) as lead_count
            FROM civix.investigative_lead
            GROUP BY case_id
        ),
        case_firs AS (
            SELECT DISTINCT ON (case_id) case_id, police_station, district
            FROM civix.fir
            ORDER BY case_id, filed_at DESC
        ),
        event_max_time AS (
            SELECT el.case_id, MAX(e.tx_start) as max_event_tx
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE el.case_id IS NOT NULL
            GROUP BY el.case_id
        ),
        evidence_max_time AS (
            SELECT case_id, MAX(tx_start) as max_evidence_tx
            FROM civix.evidence_instance
            GROUP BY case_id
        ),
        lead_max_time AS (
            SELECT case_id, MAX(created_at) as max_lead_created
            FROM civix.investigative_lead
            GROUP BY case_id
        ),
        enriched_cases AS (
            SELECT 
                c.case_id,
                c.case_number,
                c.title,
                c.investigating_unit as description,
                c.case_type::text as case_type,
                c.status::text as status,
                c.priority::text as priority,
                COALESCE(f.district, c.jurisdiction) as jurisdiction,
                COALESCE(f.police_station, c.jurisdiction) as police_station,
                COALESCE(ce.entity_count, 0) as entity_count,
                COALESCE(cev.evidence_count, 0) as evidence_count,
                COALESCE(cevt.event_count, 0) as event_count,
                COALESCE(cl.lead_count, 0) as lead_count,
                GREATEST(
                    c.updated_at,
                    c.created_at,
                    emt.max_event_tx,
                    evmt.max_evidence_tx,
                    lmt.max_lead_created
                ) as last_activity_at,
                c.created_at,
                c.updated_at,
                CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC' ELSE 'GOLDEN' END as provenance,
                CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC_BENCHMARK' ELSE 'HERO_INVESTIGATION' END as source_type
            FROM civix.investigative_case c
            LEFT JOIN case_entities ce ON c.case_id = ce.case_id
            LEFT JOIN case_evidence cev ON c.case_id = cev.case_id
            LEFT JOIN case_events cevt ON c.case_id = cevt.case_id
            LEFT JOIN case_leads cl ON c.case_id = cl.case_id
            LEFT JOIN case_firs f ON c.case_id = f.case_id
            LEFT JOIN event_max_time emt ON c.case_id = emt.case_id
            LEFT JOIN evidence_max_time evmt ON c.case_id = evmt.case_id
            LEFT JOIN lead_max_time lmt ON c.case_id = lmt.case_id
        )
        SELECT COUNT(*) OVER() as filtered_total, * 
        FROM enriched_cases c
        {where_sql}
        ORDER BY 
            (CASE WHEN c.provenance = 'GOLDEN' THEN 0 ELSE 1 END) ASC,
            {sort_col} {order_dir} {nulls_dir}
        LIMIT :limit OFFSET :offset;
    """)

    result = await session.execute(items_sql, query_params)
    rows = result.fetchall()

    filtered_total = 0
    items: List[CaseRegistryItem] = []

    for r in rows:
        m = r._mapping
        filtered_total = m["filtered_total"]
        items.append(CaseRegistryItem(
            case_id=m["case_id"],
            case_number=m["case_number"],
            title=m["title"],
            description=m["description"],
            case_type=m["case_type"],
            status=m["status"],
            priority=m["priority"],
            jurisdiction=m["jurisdiction"],
            police_station=m["police_station"],
            provenance=m["provenance"],
            source_type=m["source_type"],
            entity_count=m["entity_count"],
            evidence_count=m["evidence_count"],
            event_count=m["event_count"],
            lead_count=m["lead_count"],
            last_activity_at=m["last_activity_at"],
            created_at=m["created_at"],
            updated_at=m["updated_at"]
        ))

    total_pages = math.ceil(filtered_total / page_size) if filtered_total > 0 else 0

    # 4. Query global summary statistics across the authorized case population
    summary_sql = text("""
        WITH event_max_time AS (
            SELECT el.case_id, MAX(e.tx_start) as max_event_tx
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE el.case_id IS NOT NULL
            GROUP BY el.case_id
        ),
        evidence_max_time AS (
            SELECT case_id, MAX(tx_start) as max_evidence_tx
            FROM civix.evidence_instance
            GROUP BY case_id
        ),
        lead_max_time AS (
            SELECT case_id, MAX(created_at) as max_lead_created
            FROM civix.investigative_lead
            GROUP BY case_id
        )
        SELECT
            COUNT(*) as total_cases,
            COUNT(*) FILTER (WHERE c.status::text IN ('ACTIVE', 'OPEN')) as active_cases,
            COUNT(*) FILTER (WHERE c.priority::text = 'CRITICAL') as critical_cases,
            COUNT(*) FILTER (WHERE c.case_number NOT LIKE 'SYN-%') as golden_cases,
            COUNT(*) FILTER (WHERE c.case_number LIKE 'SYN-%') as synthetic_cases,
            COUNT(*) FILTER (WHERE (GREATEST(
                c.updated_at,
                c.created_at,
                emt.max_event_tx,
                evmt.max_evidence_tx,
                lmt.max_lead_created
            ) AT TIME ZONE 'Asia/Kolkata')::date = (NOW() AT TIME ZONE 'Asia/Kolkata')::date) as updated_today
        FROM civix.investigative_case c
        LEFT JOIN event_max_time emt ON c.case_id = emt.case_id
        LEFT JOIN evidence_max_time evmt ON c.case_id = evmt.case_id
        LEFT JOIN lead_max_time lmt ON c.case_id = lmt.case_id;
    """)

    sum_result = await session.execute(summary_sql)
    s = sum_result.fetchone()._mapping

    summary = CaseRegistrySummary(
        total_cases=s["total_cases"],
        active_cases=s["active_cases"],
        critical_cases=s["critical_cases"],
        golden_cases=s["golden_cases"],
        synthetic_cases=s["synthetic_cases"],
        updated_today=s["updated_today"]
    )

    pagination = CaseRegistryPagination(
        page=page,
        page_size=page_size,
        total=filtered_total,
        total_pages=total_pages
    )

    return CaseRegistryResponse(
        items=items,
        pagination=pagination,
        summary=summary
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

    VALID_CASE_TYPES = {'CRIMINAL', 'FINANCIAL', 'FORENSIC', 'INTELLIGENCE', 'MULTI_CASE', 'PROPERTY', 'SURVEILLANCE'}
    c_type = case_data.case_type.upper() if case_data.case_type and case_data.case_type.upper() in VALID_CASE_TYPES else 'CRIMINAL'

    # 1. Insert investigative_case FIRST
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
            "type": c_type,
            "prio": case_data.priority,
            "jur": case_data.jurisdiction,
            "unit": case_data.investigating_unit,
            "uid": user.user_id
        }
    )

    # 2. Insert case_access SECOND (satisfying FK constraint)
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

@router.get("/{case_id}/entities")
async def get_case_entities(
    case_id: str,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    real_case_id = await resolve_case_id(session, case_id)
    query = text("""
        SELECT 
            cer.role_id,
            cer.entity_id,
            cer.role,
            cer.role_basis,
            e.entity_type::text as entity_type,
            COALESCE(
                p.display_name,
                o.legal_name,
                v.registration_number,
                d.imei,
                pn.msisdn,
                cer.entity_id::text
            ) as display_name,
            p.gender::text,
            p.date_of_birth,
            p.nationality,
            p.avatar_url
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        LEFT JOIN civix.person p ON e.entity_id = p.entity_id
        LEFT JOIN civix.organization o ON e.entity_id = o.entity_id
        LEFT JOIN civix.vehicle v ON e.entity_id = v.entity_id
        LEFT JOIN civix.device d ON e.entity_id = d.entity_id
        LEFT JOIN civix.phone_number pn ON e.entity_id = pn.entity_id
        WHERE cer.case_id = :cid;
    """)
    result = await session.execute(query, {"cid": real_case_id})
    items = [
        {
            "role_id": str(r._mapping["role_id"]),
            "entity_id": str(r._mapping["entity_id"]),
            "role": r._mapping["role"],
            "role_basis": r._mapping["role_basis"],
            "entity_type": r._mapping["entity_type"],
            "display_name": r._mapping["display_name"],
            "gender": r._mapping["gender"],
            "date_of_birth": r._mapping["date_of_birth"].isoformat() if r._mapping["date_of_birth"] else None,
            "nationality": r._mapping["nationality"],
            "avatar_url": r._mapping["avatar_url"],
        }
        for r in result.fetchall()
    ]

    # Fetch assigned police officers from case_access and lead_investigator_id
    officer_query = text("""
        SELECT DISTINCT
            ca.access_id as role_id,
            u.user_id as entity_id,
            CASE WHEN c.lead_investigator_id = u.user_id THEN 'INVESTIGATING_OFFICER' ELSE 'OFFICER_IN_CHARGE' END as role,
            COALESCE(c.investigating_unit, 'Assigned Investigation Unit') as role_basis,
            'PERSON' as entity_type,
            u.display_name,
            NULL as gender,
            NULL as date_of_birth,
            'IND' as nationality
        FROM civix.case_access ca
        JOIN civix.civix_user u ON ca.user_id = u.user_id
        JOIN civix.investigative_case c ON c.case_id = ca.case_id
        WHERE ca.case_id = :cid
    """)
    officer_result = await session.execute(officer_query, {"cid": real_case_id})
    for r in officer_result.fetchall():
        m = r._mapping
        if not any(item["entity_id"] == str(m["entity_id"]) for item in items):
            disp_name = m["display_name"]
            if disp_name == "CIVIX System":
                disp_name = "Inspector Vikram S. (IO)"
            items.append({
                "role_id": str(m["role_id"]),
                "entity_id": str(m["entity_id"]),
                "role": m["role"],
                "role_basis": m["role_basis"],
                "entity_type": m["entity_type"],
                "display_name": disp_name,
                "gender": m["gender"],
                "date_of_birth": m["date_of_birth"],
                "nationality": m["nationality"],
                "avatar_url": None,
            })

    return items

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
            SELECT c.case_id, c.case_number, c.title, c.case_type, c.status, c.priority, c.jurisdiction,
                   c.investigating_unit, c.opened_at, c.created_at, c.updated_at,
                   f.fir_number, f.police_station, f.district, f.sections_invoked
            FROM civix.investigative_case c
            LEFT JOIN civix.fir f ON f.case_id = c.case_id
            WHERE c.case_id = :cid
            ORDER BY f.filed_at DESC
            LIMIT 1
        """),
        {"cid": real_case_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
    m = row._mapping
    return {
        "case_id": str(m["case_id"]),
        "case_number": m["case_number"],
        "title": m["title"],
        "case_type": m["case_type"],
        "status": m["status"],
        "priority": m["priority"],
        "jurisdiction": m["jurisdiction"],
        "investigating_unit": m["investigating_unit"],
        "opened_at": m["opened_at"].isoformat() if m["opened_at"] else None,
        "created_at": m["created_at"].isoformat() if m["created_at"] else None,
        "updated_at": m["updated_at"].isoformat() if m["updated_at"] else None,
        "fir_number": m["fir_number"],
        "police_station": m["police_station"],
        "district": m["district"],
        "sections_invoked": m["sections_invoked"]
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



async def build_pg_case_graph(
    session: AsyncSession,
    case_id: str,
    depth: int = 1,
    node_limit: int = 100,
    rel_limit: int = 200
) -> GraphResponse:
    nodes: List[GraphNode] = []
    relationships: List[GraphRelationship] = []
    node_ids: set = set()

    # 1. Root Case Node
    c_res = await session.execute(
        text("""
            SELECT case_id, case_number, title, case_type, status, priority, created_at
            FROM civix.investigative_case
            WHERE case_id = :cid
        """),
        {"cid": case_id}
    )
    c_row = c_res.first()
    if c_row:
        m = c_row._mapping
        cid_str = str(m["case_id"])
        node_ids.add(cid_str)
        nodes.append(
            GraphNode(
                id=cid_str,
                labels=["Case"],
                properties={
                    "case_id": cid_str,
                    "case_number": m["case_number"] or "",
                    "title": m["title"] or "",
                    "case_type": str(m["case_type"]) if m["case_type"] else "INVESTIGATION",
                    "status": str(m["status"]) if m["status"] else "ACTIVE",
                    "name": m["case_number"] or "Case",
                    "display_name": m["title"] or m["case_number"] or "Case"
                }
            )
        )

    # 2. Directly related entities (Level 1)
    e_res = await session.execute(
        text("""
            SELECT 
                cer.role_id,
                cer.entity_id,
                cer.role,
                cer.role_basis,
                e.entity_type::text as entity_type,
                COALESCE(
                    p.display_name,
                    o.legal_name,
                    v.registration_number,
                    d.imei,
                    pn.msisdn,
                    cer.entity_id::text
                ) as display_name
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            LEFT JOIN civix.person p ON e.entity_id = p.entity_id
            LEFT JOIN civix.organization o ON e.entity_id = o.entity_id
            LEFT JOIN civix.vehicle v ON e.entity_id = v.entity_id
            LEFT JOIN civix.device d ON e.entity_id = d.entity_id
            LEFT JOIN civix.phone_number pn ON e.entity_id = pn.entity_id
            WHERE cer.case_id = :cid
        """),
        {"cid": case_id}
    )

    cid_str = str(case_id)
    level_1_entity_ids = set()
    for r in e_res.fetchall():
        m = r._mapping
        eid_str = str(m["entity_id"])
        level_1_entity_ids.add(eid_str)
        if eid_str not in node_ids and len(nodes) < node_limit:
            node_ids.add(eid_str)
            label = m["entity_type"].title() if m["entity_type"] else "Entity"
            nodes.append(
                GraphNode(
                    id=eid_str,
                    labels=[label],
                    properties={
                        "entity_id": eid_str,
                        "display_name": m["display_name"] or eid_str,
                        "name": m["display_name"] or eid_str,
                        "entity_type": m["entity_type"] or "ENTITY"
                    }
                )
            )
        if len(relationships) < rel_limit:
            relationships.append(
                GraphRelationship(
                    id=str(m["role_id"]),
                    type=str(m["role"]) if m["role"] else "ASSOCIATED_WITH",
                    start_node=cid_str,
                    end_node=eid_str,
                    properties={
                        "role_basis": m["role_basis"] or ""
                    }
                )
            )

    # 3. Assertions (Level 1 & Level 2)
    if level_1_entity_ids:
        a_res = await session.execute(
            text("""
                SELECT assertion_id, subject_entity_id, predicate, object_entity_id, epistemic_status, ai_confidence
                FROM civix.assertion
                WHERE (subject_entity_id = ANY(:eids) OR object_entity_id = ANY(:eids))
                  AND (tx_end IS NULL)
            """),
            {"eids": list(level_1_entity_ids)}
        )

        new_entity_ids_to_fetch = set()
        pending_assertions = []

        for r in a_res.fetchall():
            m = r._mapping
            sub_id = str(m["subject_entity_id"]) if m["subject_entity_id"] else None
            obj_id = str(m["object_entity_id"]) if m["object_entity_id"] else None
            if not sub_id or not obj_id:
                continue

            if depth > 1:
                if sub_id not in node_ids:
                    new_entity_ids_to_fetch.add(sub_id)
                if obj_id not in node_ids:
                    new_entity_ids_to_fetch.add(obj_id)

            pending_assertions.append((
                str(m["assertion_id"]),
                sub_id,
                str(m["predicate"]),
                obj_id,
                float(m["ai_confidence"]) if m["ai_confidence"] is not None else 1.0,
                str(m["epistemic_status"]) if m["epistemic_status"] else "VERIFIED"
            ))

        if new_entity_ids_to_fetch and depth > 1 and len(nodes) < node_limit:
            l2_res = await session.execute(
                text("""
                    SELECT 
                        e.entity_id,
                        e.entity_type::text as entity_type,
                        COALESCE(
                            p.display_name,
                            o.legal_name,
                            v.registration_number,
                            d.imei,
                            pn.msisdn,
                            e.entity_id::text
                        ) as display_name
                    FROM civix.entity e
                    LEFT JOIN civix.person p ON e.entity_id = p.entity_id
                    LEFT JOIN civix.organization o ON e.entity_id = o.entity_id
                    LEFT JOIN civix.vehicle v ON e.entity_id = v.entity_id
                    LEFT JOIN civix.device d ON e.entity_id = d.entity_id
                    LEFT JOIN civix.phone_number pn ON e.entity_id = pn.entity_id
                    WHERE e.entity_id = ANY(:eids)
                """),
                {"eids": list(new_entity_ids_to_fetch)}
            )

            for r in l2_res.fetchall():
                m = r._mapping
                eid_str = str(m["entity_id"])
                if eid_str not in node_ids and len(nodes) < node_limit:
                    node_ids.add(eid_str)
                    label = m["entity_type"].title() if m["entity_type"] else "Entity"
                    nodes.append(
                        GraphNode(
                            id=eid_str,
                            labels=[label],
                            properties={
                                "entity_id": eid_str,
                                "display_name": m["display_name"] or eid_str,
                                "name": m["display_name"] or eid_str,
                                "entity_type": m["entity_type"] or "ENTITY"
                            }
                        )
                    )

        for ass_id, sub_id, pred, obj_id, conf, ep_status in pending_assertions:
            if sub_id in node_ids and obj_id in node_ids and len(relationships) < rel_limit:
                relationships.append(
                    GraphRelationship(
                        id=ass_id,
                        type=pred,
                        start_node=sub_id,
                        end_node=obj_id,
                        properties={
                            "confidence": conf,
                            "epistemic_status": ep_status
                        }
                    )
                )

    meta = GraphMetadata(
        requested_depth=depth,
        max_depth=5,
        node_limit=node_limit,
        relationship_limit=rel_limit,
        nodes_returned=len(nodes),
        relationships_returned=len(relationships),
        truncated=(len(nodes) >= node_limit or len(relationships) >= rel_limit)
    )

    return GraphResponse(nodes=nodes, relationships=relationships, metadata=meta)


@router.get("/{case_id}/graph", response_model=GraphResponse)
async def get_case_graph(
    case_id: str,
    depth: int = Query(2, ge=1, le=5, description="Traversal depth (max 5)"),
    node_limit: int = Query(100, ge=1, le=500, description="Max nodes to return"),
    rel_limit: int = Query(200, ge=1, le=1000, description="Max relationships to return"),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    pg_session: AsyncSession = Depends(get_rls_session),
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session)
):
    real_case_id = await resolve_case_id(pg_session, case_id)

    # 1. Verify root case authorization through PostgreSQL RLS
    verify_result = await pg_session.execute(
        text("SELECT 1 FROM civix.investigative_case WHERE case_id = :cid"),
        {"cid": real_case_id}
    )
    if not verify_result.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # 2. Fetch full ACL (all accessible case_ids) for the user
    acl_result = await pg_session.execute(
        text("SELECT case_id FROM civix.investigative_case")
    )
    accessible_case_ids = [str(row[0]) for row in acl_result.fetchall()]

    # 3. Try Neo4j graph if session is active
    if neo4j_session is not None:
        try:
            graph = await Neo4jQueryService.get_case_graph(
                session=neo4j_session,
                case_id=str(real_case_id),
                accessible_case_ids=accessible_case_ids,
                depth=depth,
                node_limit=node_limit,
                rel_limit=rel_limit
            )
            if graph and graph.nodes:
                return graph
        except Exception as e:
            logger.warning(f"Neo4j graph query failed ({e}), falling back to PostgreSQL graph builder.")

    # 4. Fallback to PostgreSQL Graph Builder
    return await build_pg_case_graph(
        session=pg_session,
        case_id=str(real_case_id),
        depth=depth,
        node_limit=node_limit,
        rel_limit=rel_limit
    )

