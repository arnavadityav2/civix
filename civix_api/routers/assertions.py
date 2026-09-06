"""
CIVIX 2.0 — Investigator Assertion (Proposal) Router
Graph Workspace Backend Remediation — Phase 1 (B-01, B-02, B-03, B-04)
Date: 2026-09-06

PURPOSE:
    Provides the backend-authoritative pathway for investigators to PROPOSE
    relationships between entities, and for supervisors to REVIEW those proposals.

    This implements the investigator → PostgreSQL → outbox → CDC → Neo4j pipeline
    for human-authored assertions, with explicit lifecycle states.

EPISTEMIC LIFECYCLE:
    INVESTIGATOR                    → PROPOSED (PostgreSQL only, no Neo4j)
    SUPERVISOR ACCEPTS              → ACCEPTED_BY_SUPERVISOR (→ outbox → Neo4j via INVESTIGATOR_ASSERTED edge)
    SUPERVISOR REJECTS              → REJECTED (PostgreSQL only, any prior Neo4j edge removed)

INVARIANTS:
    INV-01: Hypothesis stances live in hypothesis_support, not here.
    INV-08: AI cannot confirm — and investigator proposals cannot self-confirm.
    INV-18: Predicates are strictly enum-controlled (predicate_enum).
    ADR-REM-01: Proposals use existing semantic predicates + lifecycle columns.
    ADR-REM-02: PROPOSED → NOT projected to Neo4j.
    ADR-REM-03: ACCEPTED → projected as INVESTIGATOR_ASSERTED edge (not ASSERTED_BY/ASSERTS).

ENDPOINTS:
    POST   /api/v1/cases/{case_id}/assertions
           Create a new investigator-proposed relationship.
           Requires WRITE or ADMIN on case.

    POST   /api/v1/cases/{case_id}/assertions/{assertion_id}/review
           Supervisor approves or rejects a PROPOSED assertion.
           Requires ADMIN or SUPERVISOR_ADMIN role.

    GET    /api/v1/cases/{case_id}/assertions/proposed
           List all pending PROPOSED assertions for a case.
           Requires READ+ on case.
"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.routers.cases import resolve_case_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["investigator-assertions"],
)

# ---------------------------------------------------------------------------
# Allowed predicates for investigator proposals.
# This list mirrors the predicate_enum values in the database.
# INV-18: free-text predicates are banned. Only enum values are accepted.
# If new predicates are added to the DB enum, add them here too.
# ---------------------------------------------------------------------------
ALLOWED_INVESTIGATOR_PREDICATES = {
    "CALLED",
    "MESSAGED",
    "CO_LOCATED",
    "REGISTERED_TO",
    "OWNED_BY",
    "DRIVER_OF",
    "OWNS",
    "MEMBER_OF",
    "EMPLOYED_BY",
    "ASSOCIATED_WITH",
    "KNOWN_ASSOCIATE_OF",
    "OBSERVED_AT",
    "LINKED_TO",
    "TRANSFERRED_TO",
    "RECEIVED_FROM",
    "PARTICIPATED_IN",
    "RELATED_TO",
    "ALIAS_OF",
    "LIVES_AT",
    "WORKS_AT",
    "OPERATES",
    "CONTROLS",
    "FINANCES",
    "DIRECTED_BY",
    "HAS_SIM",
    "USES_DEVICE",
    "SAME_VEHICLE_AS",
    "TRANSACTED_WITH",
    "PRESENT_AT",
}

# Supervisor and admin roles that may review proposals
REVIEWER_ROLES = {"ADMIN", "SUPERVISOR_ADMIN"}

# Roles allowed to create proposals
PROPOSAL_ALLOWED_PERMISSIONS = {"WRITE", "ADMIN"}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class InvestigatorAssertionRequest(BaseModel):
    """
    Request body for creating an investigator-proposed relationship.
    All fields are mandatory — no optional justification, no anonymous proposals.
    """
    subject_entity_id: UUID = Field(
        ..., description="UUID of the source entity."
    )
    predicate: str = Field(
        ..., description="Semantic relationship type. Must be an existing predicate_enum value."
    )
    object_entity_id: UUID = Field(
        ..., description="UUID of the target entity."
    )
    investigator_justification: str = Field(
        ..., min_length=10, max_length=4000,
        description="Non-empty investigator rationale. Minimum 10 characters. Required by invariant."
    )
    evidence_instance_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Optional list of evidence_instance UUIDs supporting this proposal."
    )

    @field_validator("predicate")
    @classmethod
    def validate_predicate(cls, v: str) -> str:
        if v.upper() not in ALLOWED_INVESTIGATOR_PREDICATES:
            raise ValueError(
                f"Predicate '{v}' is not a valid predicate_enum value. "
                f"INV-18 prohibits free-text predicates. "
                f"Allowed values: {sorted(ALLOWED_INVESTIGATOR_PREDICATES)}"
            )
        return v.upper()

    @field_validator("investigator_justification")
    @classmethod
    def validate_justification_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("investigator_justification must not be blank.")
        return v.strip()


class InvestigatorAssertionResponse(BaseModel):
    """Returned after a successful investigator proposal creation."""
    assertion_id: UUID
    case_id: UUID
    subject_entity_id: UUID
    predicate: str
    object_entity_id: UUID
    assertion_origin: str
    proposal_status: str
    epistemic_status: str
    investigator_justification: str
    asserted_by: Optional[UUID]
    authorized_case_ids: List[str]
    created_at: datetime
    message: str


class ReviewRequest(BaseModel):
    """Supervisor review decision."""
    decision: Literal["ACCEPT", "REJECT"] = Field(
        ..., description="ACCEPT transitions to ACCEPTED_BY_SUPERVISOR. REJECT transitions to REJECTED."
    )
    review_notes: Optional[str] = Field(
        default=None, max_length=2000,
        description="Optional notes from the supervisor explaining the decision."
    )


class ReviewResponse(BaseModel):
    assertion_id: UUID
    previous_status: str
    new_status: str
    reviewed_by: UUID
    reviewed_at: datetime
    message: str


class ProposedAssertionListItem(BaseModel):
    assertion_id: UUID
    subject_entity_id: UUID
    predicate: str
    object_entity_id: UUID
    investigator_justification: str
    asserted_by: Optional[UUID]
    created_at: datetime
    proposal_status: str


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

async def _check_case_write_access(session: AsyncSession, case_id: UUID, user_id: UUID) -> None:
    """Verify the user has WRITE or ADMIN permission on the case."""
    result = await session.execute(
        text("""
            SELECT permission_level
            FROM civix.case_access
            WHERE case_id = :cid AND user_id = :uid
              AND is_revoked = FALSE
              AND (valid_until IS NULL OR valid_until > now())
        """),
        {"cid": case_id, "uid": user_id}
    )
    row = result.first()
    if not row or row.permission_level not in PROPOSAL_ALLOWED_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Requires WRITE or ADMIN access to create an investigator proposal."
        )


async def _check_case_read_access(session: AsyncSession, case_id: UUID, user_id: UUID) -> None:
    """Verify the user has any active access on the case."""
    result = await session.execute(
        text("""
            SELECT 1 FROM civix.case_access
            WHERE case_id = :cid AND user_id = :uid
              AND is_revoked = FALSE
              AND (valid_until IS NULL OR valid_until > now())
        """),
        {"cid": case_id, "uid": user_id}
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: No active access to this case."
        )


async def _verify_entity_in_case_context(
    session: AsyncSession, entity_id: UUID, case_id: UUID
) -> None:
    """
    Verify that the given entity is visible in the context of the given case.
    An entity is in context if it has an active role in the case.
    This prevents investigators from creating proposals involving entities they cannot see.
    """
    result = await session.execute(
        text("""
            SELECT 1 FROM civix.case_entity_role
            WHERE entity_id = :eid AND case_id = :cid AND tx_end IS NULL
        """),
        {"eid": entity_id, "cid": case_id}
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Entity {entity_id} is not active in case context. "
                   f"Only entities with active roles in this case may be connected."
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{case_id}/assertions",
    response_model=InvestigatorAssertionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an investigator-proposed relationship between entities",
    description=(
        "Allows an investigator to propose a semantic relationship between two entities "
        "in a case context. The proposal is PROPOSED state and does NOT become part of "
        "the authoritative graph until a supervisor accepts it. "
        "INV-18: All predicates must be existing enum values — no free-text."
    ),
)
async def create_investigator_assertion(
    case_id: str,
    body: InvestigatorAssertionRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    B-01 REMEDIATION: The missing investigator proposal API endpoint.

    Creates an assertion with:
        assertion_origin = INVESTIGATOR_PROPOSED
        proposal_status  = PROPOSED
        epistemic_status = POSSIBLE (investigator cannot self-assign higher confidence)
        asserted_by      = current user

    The assertion is PostgreSQL-only at this stage. It will NOT be projected
    to Neo4j until a supervisor explicitly accepts it.
    """
    real_case_id = await resolve_case_id(session, case_id)

    # 1. Authorization: user must have WRITE/ADMIN on the case
    await _check_case_write_access(session, real_case_id, user.user_id)

    # 2. Validate subject != object (no self-loops)
    if body.subject_entity_id == body.object_entity_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="subject_entity_id and object_entity_id must be different entities."
        )

    # 3. Verify both entities are active in the case context
    await _verify_entity_in_case_context(session, body.subject_entity_id, real_case_id)
    await _verify_entity_in_case_context(session, body.object_entity_id, real_case_id)

    # 4. Validate evidence instances if provided
    if body.evidence_instance_ids:
        for eid in body.evidence_instance_ids:
            ev_result = await session.execute(
                text("""
                    SELECT 1 FROM civix.evidence_instance
                    WHERE artifact_id = :eid AND case_id = :cid
                """),
                {"eid": eid, "cid": real_case_id}
            )
            if not ev_result.first():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Evidence instance {eid} is not found in this case."
                )

    # 5. Insert the investigator-proposed assertion
    assertion_id = uuid4()
    now = datetime.now(timezone.utc)

    await session.execute(
        text("""
            INSERT INTO civix.assertion (
                assertion_id,
                subject_entity_id,
                predicate,
                object_entity_id,
                epistemic_status,
                ai_confidence,
                asserted_by,
                authorized_case_ids,
                assertion_origin,
                proposal_status,
                investigator_justification,
                tx_start
            ) VALUES (
                :assertion_id,
                :subject_entity_id,
                :predicate,
                :object_entity_id,
                'POSSIBLE',
                NULL,
                :asserted_by,
                ARRAY[:case_id]::UUID[],
                'INVESTIGATOR_PROPOSED',
                'PROPOSED',
                :justification,
                now()
            )
        """),
        {
            "assertion_id": assertion_id,
            "subject_entity_id": body.subject_entity_id,
            "predicate": body.predicate,
            "object_entity_id": body.object_entity_id,
            "asserted_by": user.user_id,
            "case_id": real_case_id,
            "justification": body.investigator_justification.strip(),
        }
    )

    # 6. Write audit event
    await session.execute(
        text("""
            INSERT INTO civix.audit_event (
                user_id, action, target_table, target_id, metadata
            ) VALUES (
                :user_id, 'WRITE', 'civix.assertion', :target_id,
                jsonb_build_object(
                    'assertion_origin', 'INVESTIGATOR_PROPOSED',
                    'proposal_status', 'PROPOSED',
                    'predicate', CAST(:predicate AS TEXT)
                )
            )
        """),
        {
            "user_id": user.user_id,
            "target_id": assertion_id,
            "predicate": body.predicate,
        }
    )

    await session.commit()

    logger.info(
        f"Investigator proposal created: assertion_id={assertion_id}, "
        f"case_id={real_case_id}, proposer={user.user_id}, predicate={body.predicate}"
    )

    return InvestigatorAssertionResponse(
        assertion_id=assertion_id,
        case_id=real_case_id,
        subject_entity_id=body.subject_entity_id,
        predicate=body.predicate,
        object_entity_id=body.object_entity_id,
        assertion_origin="INVESTIGATOR_PROPOSED",
        proposal_status="PROPOSED",
        epistemic_status="POSSIBLE",
        investigator_justification=body.investigator_justification.strip(),
        asserted_by=user.user_id,
        authorized_case_ids=[str(real_case_id)],
        created_at=now,
        message=(
            "Proposal created as PROPOSED. Awaiting supervisor review. "
            "This relationship is NOT part of the authoritative graph until accepted."
        ),
    )


@router.post(
    "/{case_id}/assertions/{assertion_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Supervisor review: accept or reject an investigator-proposed relationship",
    description=(
        "Transitions a PROPOSED assertion to ACCEPTED_BY_SUPERVISOR (which triggers "
        "Neo4j projection via the outbox/CDC pipeline) or REJECTED (no projection). "
        "Requires ADMIN or SUPERVISOR_ADMIN role. "
        "An investigator cannot accept their own proposal unless they hold a reviewer role."
    ),
)
async def review_investigator_assertion(
    case_id: str,
    assertion_id: UUID,
    body: ReviewRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    Supervisor review endpoint. Implements the PROPOSED → ACCEPTED_BY_SUPERVISOR / REJECTED transition.

    On ACCEPT:
        - Sets proposal_status = ACCEPTED_BY_SUPERVISOR
        - Sets reviewed_by, reviewed_at
        - The existing assertion outbox trigger fires (trg_assertion_upsert_outbox)
          on UPDATE OF proposal_status → CDC worker picks it up → Neo4j projection

    On REJECT:
        - Sets proposal_status = REJECTED
        - The assertion outbox trigger fires → CDC worker picks it up
        - Neo4j projection service removes any INVESTIGATOR_ASSERTED edge (tombstone)

    Invalid transitions are rejected at the API layer.
    """
    real_case_id = await resolve_case_id(session, case_id)

    # 1. Authorization: only ADMIN or SUPERVISOR_ADMIN may review proposals
    if user.role not in REVIEWER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Requires role ADMIN or SUPERVISOR_ADMIN to review proposals. Your role: {user.role}"
        )

    # 2. Verify the assertion exists and belongs to this case
    result = await session.execute(
        text("""
            SELECT assertion_id, asserted_by, proposal_status, assertion_origin, predicate
            FROM civix.assertion
            WHERE assertion_id = :aid
              AND :case_id = ANY(authorized_case_ids)
              AND tx_end IS NULL
        """),
        {"aid": assertion_id, "case_id": real_case_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assertion {assertion_id} not found in case {real_case_id}."
        )

    if row.assertion_origin != "INVESTIGATOR_PROPOSED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assertion {assertion_id} is not an investigator proposal (origin: {row.assertion_origin}). Only INVESTIGATOR_PROPOSED assertions can be reviewed."
        )

    current_status = row.proposal_status

    # 3. Validate state transition
    if current_status != "PROPOSED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Assertion {assertion_id} is in state '{current_status}'. "
                f"Only PROPOSED assertions can be reviewed. "
                f"Invalid transition: {current_status} → {body.decision}."
            )
        )

    # 4. Determine new status
    new_status = "ACCEPTED_BY_SUPERVISOR" if body.decision == "ACCEPT" else "REJECTED"
    now = datetime.now(timezone.utc)

    # 5. Update assertion — this UPDATE fires the outbox trigger (trg_assertion_upsert_outbox)
    #    which will emit to the CDC queue → Neo4j projection service will handle projection/tombstone
    await session.execute(
        text("""
            UPDATE civix.assertion
            SET proposal_status = :new_status,
                reviewed_by = :reviewed_by,
                reviewed_at = :reviewed_at
            WHERE assertion_id = :aid
              AND tx_end IS NULL
        """),
        {
            "new_status": new_status,
            "reviewed_by": user.user_id,
            "reviewed_at": now,
            "aid": assertion_id,
        }
    )

    # 6. Write audit event
    await session.execute(
        text("""
            INSERT INTO civix.audit_event (
                user_id, action, target_table, target_id, metadata
            ) VALUES (
                :user_id, 'SUPERVISOR_REVIEW', 'civix.assertion', :target_id,
                jsonb_build_object(
                    'previous_status', CAST(:previous_status AS TEXT),
                    'new_status', CAST(:new_status AS TEXT),
                    'predicate', CAST(:predicate AS TEXT),
                    'review_notes', CAST(:review_notes AS TEXT)
                )
            )
        """),
        {
            "user_id": user.user_id,
            "target_id": assertion_id,
            "previous_status": current_status,
            "new_status": new_status,
            "predicate": row.predicate,
            "review_notes": body.review_notes,
        }
    )

    await session.commit()

    logger.info(
        f"Supervisor review: assertion_id={assertion_id}, "
        f"reviewer={user.user_id}, decision={body.decision}, "
        f"new_status={new_status}. "
        f"{'Neo4j projection queued via outbox.' if new_status == 'ACCEPTED_BY_SUPERVISOR' else 'Neo4j tombstone queued via outbox.'}"
    )

    return ReviewResponse(
        assertion_id=assertion_id,
        previous_status=current_status,
        new_status=new_status,
        reviewed_by=user.user_id,
        reviewed_at=now,
        message=(
            "Assertion accepted. Queued for Neo4j projection via CDC pipeline."
            if new_status == "ACCEPTED_BY_SUPERVISOR"
            else "Assertion rejected. Will not be projected to the graph."
        ),
    )


@router.get(
    "/{case_id}/assertions/proposed",
    response_model=List[ProposedAssertionListItem],
    summary="List pending investigator proposals for a case",
)
async def list_proposed_assertions(
    case_id: str,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session),
):
    """
    Returns all PROPOSED (unreviewed) investigator assertions for the given case.
    Requires any active access on the case.
    """
    real_case_id = await resolve_case_id(session, case_id)
    await _check_case_read_access(session, real_case_id, user.user_id)

    result = await session.execute(
        text("""
            SELECT assertion_id, subject_entity_id, predicate, object_entity_id,
                   investigator_justification, asserted_by, tx_start as created_at,
                   proposal_status
            FROM civix.assertion
            WHERE :case_id = ANY(authorized_case_ids)
              AND assertion_origin = 'INVESTIGATOR_PROPOSED'
              AND proposal_status = 'PROPOSED'
              AND tx_end IS NULL
            ORDER BY tx_start DESC
        """),
        {"case_id": real_case_id}
    )
    rows = result.fetchall()
    return [
        ProposedAssertionListItem(
            assertion_id=row.assertion_id,
            subject_entity_id=row.subject_entity_id,
            predicate=row.predicate,
            object_entity_id=row.object_entity_id,
            investigator_justification=row.investigator_justification,
            asserted_by=row.asserted_by,
            created_at=row.created_at,
            proposal_status=row.proposal_status,
        )
        for row in rows
    ]
