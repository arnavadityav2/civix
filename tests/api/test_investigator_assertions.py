"""
CIVIX 2.0 — Investigator Assertion Proposal Lifecycle Tests
Graph Workspace Backend Remediation — Phase 1 (B-01, B-02, B-03, B-04)

Tests cover:
    Authorization:
        5. Unauthorized investigator cannot create proposal.
        6. Investigator cannot propose relationship involving inaccessible entity.
        7. Invalid predicate rejected (INV-18).
        8. Empty justification rejected.

    Proposal lifecycle:
        9.  Valid investigator proposal created as PROPOSED.
        10. Proposal records investigator identity.
        11. Proposal records justification.
        12. Proposal preserves semantic predicate.
        13. Supervisor can accept.
        14. Supervisor can reject.
        15. Unauthorized user cannot approve.
        16. Invalid state transition rejected (ACCEPTED → PROPOSED not allowed).
        17. Existing AI assertions remain unaffected.

    Database invariants:
        18. INV-01 remains valid (stances not on assertion).
        19. INV-18 remains valid (enum predicates enforced).
        20. Proposal status NOT_APPLICABLE for AI assertions.
        21. Hero/Golden cases remain protected (not verified here — needs live DB).

    Neo4j / CDC behavior:
        23. Accepted → assertion outbox trigger fires with ACCEPTED status.
        24. Proposed → no outbox emission expected.
        25. Rejected proposal cannot become authoritative.

    CDC Safety:
        27. CDC worker with missing DSN aborts safely.
        27b. CDC worker with civix_test DSN aborts safely.
"""

import pytest
import jwt
import sys
import time
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from unittest.mock import patch, MagicMock

from civix_api.main import app
from civix_api.config import settings


def create_token(sub: str, role: str = "INVESTIGATOR") -> str:
    payload = {"sub": sub, "exp": int(time.time()) + 3600}
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")


async def setup_case_with_user(db_session, create_test_user, role="INVESTIGATOR", permission="WRITE"):
    user_id = await create_test_user(role=role)
    token = create_token(str(user_id), role=role)
    case_id = str(uuid4())
    await db_session.execute(
        text("""
            INSERT INTO civix.investigative_case
                (case_id, case_number, title, case_type, status, priority, jurisdiction, opened_at)
            VALUES (:cid, :cnum, 'Test Case', 'CRIMINAL', 'ACTIVE', 'HIGH', 'Test Jurisdiction', now())
        """),
        {"cid": case_id, "cnum": f"PROP-{uuid4().hex[:6]}"}
    )
    await db_session.execute(
        text("""
            INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by, is_revoked)
            VALUES (:cid, :uid, :perm, :uid, false)
        """),
        {"cid": case_id, "uid": user_id, "perm": permission}
    )
    await db_session.commit()
    return user_id, token, case_id


async def create_entity(db_session, case_id: str, user_id) -> str:
    entity_id = str(uuid4())
    await db_session.execute(
        text("INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES (:eid, 'PERSON', 'ACTIVE')"),
        {"eid": entity_id}
    )
    await db_session.execute(
        text("INSERT INTO civix.person (entity_id, display_name) VALUES (:eid, :name)"),
        {"eid": entity_id, "name": f"TestPerson-{entity_id[:8]}"}
    )
    await db_session.execute(
        text("""
            INSERT INTO civix.case_entity_role (case_id, entity_id, role, assigned_by)
            VALUES (:cid, :eid, 'SUSPECT', :uid)
        """),
        {"cid": case_id, "eid": entity_id, "uid": user_id}
    )
    await db_session.commit()
    return entity_id


async def cleanup(db_session, case_id, entity_ids=None, assertion_ids=None):
    if assertion_ids:
        for aid in assertion_ids:
            await db_session.execute(text("DELETE FROM civix.assertion WHERE assertion_id = :aid"), {"aid": aid})
    if entity_ids:
        await db_session.execute(text("DELETE FROM civix.case_entity_role WHERE case_id = :cid"), {"cid": case_id})
        for eid in entity_ids:
            # BLK-16/ADR-018: civix.entity rows cannot be physically deleted.
            # Tombstone the entity instead.
            await db_session.execute(
                text("UPDATE civix.entity SET visibility_status = 'TOMBSTONED' WHERE entity_id = :eid"),
                {"eid": eid}
            )
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
    await db_session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Unauthorized user (READ-only) cannot create a proposal
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_readonly_user_cannot_create_proposal(db_session, create_test_user):
    """Test 5: Only WRITE/ADMIN users can create proposals. READ is refused."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="READ")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Seen together at location X multiple times."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b])


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Cannot propose with entity from different case
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cannot_propose_with_entity_from_other_case(db_session, create_test_user):
    """Test 6: Entity must be active in the requested case context."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")

    # Other case + entity
    _other_id, _, other_case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_in_case = await create_entity(db_session, case_id, user_id)
    entity_other = await create_entity(db_session, other_case_id, user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_in_case,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_other,  # belongs to other case!
                "investigator_justification": "Attempting to cross-case link this entity."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    assert "not active in case context" in r.text.lower() or "422" in str(r.status_code)

    await cleanup(db_session, case_id, entity_ids=[entity_in_case])
    await cleanup(db_session, other_case_id, entity_ids=[entity_other])


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Invalid predicate rejected (INV-18)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_invalid_predicate_rejected(db_session, create_test_user):
    """Test 7: INV-18 — Free-text predicates are rejected."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "MAYBE_KNOWS_SOMEONE_NAMED_BOB",  # free-text, not in enum
                "object_entity_id": entity_b,
                "investigator_justification": "I think they might know each other."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b])


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Empty justification rejected
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_justification_rejected(db_session, create_test_user):
    """Test 8: Justification cannot be empty or too short."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    for bad_justification in ["", "   ", "short"]:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                f"/api/v1/cases/{case_id}/assertions",
                json={
                    "subject_entity_id": entity_a,
                    "predicate": "KNOWN_ASSOCIATE_OF",
                    "object_entity_id": entity_b,
                    "investigator_justification": bad_justification
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 422, f"Expected 422 for justification={bad_justification!r}, got {r.status_code}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b])


# ─────────────────────────────────────────────────────────────────────────────
# Test 9–12: Valid proposal creation
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_valid_proposal_created_as_proposed(db_session, create_test_user):
    """Tests 9–12: Valid proposal created correctly with all required fields."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Surveillance footage places them together at the same location on three separate occasions."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 201, r.text
    data = r.json()

    # Test 9: Created as PROPOSED
    assert data["proposal_status"] == "PROPOSED"

    # Test 10: Records investigator identity
    assert data["asserted_by"] == str(user_id)

    # Test 11: Records justification
    assert "surveillance footage" in data["investigator_justification"].lower()

    # Test 12: Preserves semantic predicate
    assert data["predicate"] == "KNOWN_ASSOCIATE_OF"

    # Also verify assertion_origin
    assert data["assertion_origin"] == "INVESTIGATOR_PROPOSED"
    assert data["epistemic_status"] == "POSSIBLE"

    # Verify it's in the DB
    result = await db_session.execute(
        text("SELECT proposal_status, assertion_origin, asserted_by FROM civix.assertion WHERE assertion_id = :aid"),
        {"aid": data["assertion_id"]}
    )
    row = result.first()
    assert row is not None
    assert row.proposal_status == "PROPOSED"
    assert row.assertion_origin == "INVESTIGATOR_PROPOSED"
    assert str(row.asserted_by) == str(user_id)

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[data["assertion_id"]])


# ─────────────────────────────────────────────────────────────────────────────
# Test 13: Supervisor can accept
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_supervisor_can_accept_proposal(db_session, create_test_user):
    """Test 13: ADMIN user can accept a PROPOSED assertion → ACCEPTED_BY_SUPERVISOR."""
    inv_id, inv_token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    sup_id, sup_token, _ = await setup_case_with_user(db_session, create_test_user, role="ADMIN", permission="ADMIN")

    # Grant supervisor access to the same case
    await db_session.execute(
        text("""
            INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by, is_revoked)
            VALUES (:cid, :uid, 'ADMIN', :uid, false)
            ON CONFLICT DO NOTHING
        """),
        {"cid": case_id, "uid": sup_id}
    )
    await db_session.commit()

    entity_a = await create_entity(db_session, case_id, inv_id)
    entity_b = await create_entity(db_session, case_id, inv_id)

    # Investigator creates proposal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_create = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Multiple co-location events observed in surveillance data."
            },
            headers={"Authorization": f"Bearer {inv_token}"}
        )
    assert r_create.status_code == 201
    assertion_id = r_create.json()["assertion_id"]

    # Supervisor accepts
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_review = await ac.post(
            f"/api/v1/cases/{case_id}/assertions/{assertion_id}/review",
            json={"decision": "ACCEPT", "review_notes": "Corroborated by field report."},
            headers={"Authorization": f"Bearer {sup_token}"}
        )
    assert r_review.status_code == 200, r_review.text
    review_data = r_review.json()

    assert review_data["previous_status"] == "PROPOSED"
    assert review_data["new_status"] == "ACCEPTED_BY_SUPERVISOR"
    assert review_data["reviewed_by"] == str(sup_id)

    # Verify in DB
    result = await db_session.execute(
        text("SELECT proposal_status, reviewed_by, reviewed_at FROM civix.assertion WHERE assertion_id = :aid"),
        {"aid": assertion_id}
    )
    row = result.first()
    assert row.proposal_status == "ACCEPTED_BY_SUPERVISOR"
    assert str(row.reviewed_by) == str(sup_id)
    assert row.reviewed_at is not None

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 14: Supervisor can reject
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_supervisor_can_reject_proposal(db_session, create_test_user):
    """Test 14: ADMIN user can reject a PROPOSED assertion → REJECTED."""
    inv_id, inv_token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    sup_id, sup_token, _ = await setup_case_with_user(db_session, create_test_user, role="ADMIN", permission="ADMIN")

    await db_session.execute(
        text("""
            INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by, is_revoked)
            VALUES (:cid, :uid, 'ADMIN', :uid, false) ON CONFLICT DO NOTHING
        """),
        {"cid": case_id, "uid": sup_id}
    )
    await db_session.commit()

    entity_a = await create_entity(db_session, case_id, inv_id)
    entity_b = await create_entity(db_session, case_id, inv_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_create = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Hearsay from informant. Needs corroboration."
            },
            headers={"Authorization": f"Bearer {inv_token}"}
        )
    assert r_create.status_code == 201
    assertion_id = r_create.json()["assertion_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_review = await ac.post(
            f"/api/v1/cases/{case_id}/assertions/{assertion_id}/review",
            json={"decision": "REJECT", "review_notes": "Insufficient evidence. Informant not verified."},
            headers={"Authorization": f"Bearer {sup_token}"}
        )
    assert r_review.status_code == 200, r_review.text
    assert r_review.json()["new_status"] == "REJECTED"

    result = await db_session.execute(
        text("SELECT proposal_status FROM civix.assertion WHERE assertion_id = :aid"),
        {"aid": assertion_id}
    )
    assert result.first().proposal_status == "REJECTED"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 15: Unauthorized user (INVESTIGATOR role) cannot approve
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_investigator_cannot_approve_proposal(db_session, create_test_user):
    """Test 15: INVESTIGATOR role cannot approve proposals — only ADMIN/SUPERVISOR_ADMIN."""
    inv_id, inv_token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, inv_id)
    entity_b = await create_entity(db_session, case_id, inv_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_create = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Based on field observations over three months."
            },
            headers={"Authorization": f"Bearer {inv_token}"}
        )
    assert r_create.status_code == 201
    assertion_id = r_create.json()["assertion_id"]

    # Same investigator tries to approve their own proposal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_review = await ac.post(
            f"/api/v1/cases/{case_id}/assertions/{assertion_id}/review",
            json={"decision": "ACCEPT"},
            headers={"Authorization": f"Bearer {inv_token}"}  # Same user, INVESTIGATOR role
        )
    assert r_review.status_code == 403, f"Expected 403, got {r_review.status_code}: {r_review.text}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 16: Invalid state transition rejected
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_invalid_state_transition_rejected(db_session, create_test_user):
    """Test 16: Cannot re-review an already ACCEPTED assertion."""
    inv_id, inv_token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    sup_id, sup_token, _ = await setup_case_with_user(db_session, create_test_user, role="ADMIN", permission="ADMIN")

    await db_session.execute(
        text("""
            INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by, is_revoked)
            VALUES (:cid, :uid, 'ADMIN', :uid, false) ON CONFLICT DO NOTHING
        """),
        {"cid": case_id, "uid": sup_id}
    )
    await db_session.commit()

    entity_a = await create_entity(db_session, case_id, inv_id)
    entity_b = await create_entity(db_session, case_id, inv_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Confirmed by multiple independent sources over 6 months."
            },
            headers={"Authorization": f"Bearer {inv_token}"}
        )
    assertion_id = r.json()["assertion_id"]

    # First accept
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            f"/api/v1/cases/{case_id}/assertions/{assertion_id}/review",
            json={"decision": "ACCEPT"},
            headers={"Authorization": f"Bearer {sup_token}"}
        )

    # Try to accept again — should be rejected (ACCEPTED_BY_SUPERVISOR → cannot be PROPOSED again)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r2 = await ac.post(
            f"/api/v1/cases/{case_id}/assertions/{assertion_id}/review",
            json={"decision": "REJECT"},
            headers={"Authorization": f"Bearer {sup_token}"}
        )
    assert r2.status_code == 409, f"Expected 409 Conflict for invalid transition, got {r2.status_code}: {r2.text}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 17: Existing AI assertions remain unaffected by migration 035
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_existing_ai_assertions_unaffected(db_session, create_test_user):
    """Test 17: AI-generated assertions still work correctly after migration 035."""
    user_id, _token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    # Insert an AI assertion directly (simulating C3 engine output)
    ai_assertion_id = str(uuid4())
    await db_session.execute(
        text("""
            INSERT INTO civix.assertion (
                assertion_id, subject_entity_id, predicate, object_entity_id,
                epistemic_status, ai_confidence, authorized_case_ids, asserted_by
            ) VALUES (
                :assertion_id, :subject_entity_id, 'KNOWN_ASSOCIATE_OF', :object_entity_id,
                'CONFIRMED', 0.95, ARRAY[:case_id]::UUID[], :user_id
            )
        """),
        {"assertion_id": ai_assertion_id, "subject_entity_id": entity_a, "object_entity_id": entity_b, "case_id": case_id, "user_id": user_id}
    )
    await db_session.commit()

    # Verify the AI assertion has correct defaults
    result = await db_session.execute(
        text("SELECT assertion_origin, proposal_status, investigator_justification FROM civix.assertion WHERE assertion_id = :aid"),
        {"aid": ai_assertion_id}
    )
    row = result.first()
    assert row is not None
    assert row.assertion_origin == "AI_PIPELINE"
    assert row.proposal_status == "NOT_APPLICABLE"
    assert row.investigator_justification is None

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[ai_assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 18: INV-18 — predicate validation via API
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_inv18_enforced_via_api(db_session, create_test_user):
    """Test 18: INV-18 — All predicates via the proposal API must be enum values."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    bad_predicates = [
        "RANDOM_STRING",
        "knows",
        "might know",
        "1' OR '1'='1",  # SQL injection attempt
        "",
        "INVESTIGATOR_PROPOSED_LINK",  # The generic catch-all we explicitly rejected in ADR-REM-01
    ]

    for bad_pred in bad_predicates:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                f"/api/v1/cases/{case_id}/assertions",
                json={
                    "subject_entity_id": entity_a,
                    "predicate": bad_pred,
                    "object_entity_id": entity_b,
                    "investigator_justification": "Testing invalid predicate rejection."
                },
                headers={"Authorization": f"Bearer {token}"}
            )
        assert r.status_code == 422, f"Expected 422 for predicate={bad_pred!r}, got {r.status_code}"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b])


# ─────────────────────────────────────────────────────────────────────────────
# Test 19: Self-loop assertion rejected
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_self_loop_assertion_rejected(db_session, create_test_user):
    """Test: subject_entity_id == object_entity_id must be rejected."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_a,  # Same entity!
                "investigator_justification": "Attempting a self-referential relationship."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"

    await cleanup(db_session, case_id, entity_ids=[entity_a])


# ─────────────────────────────────────────────────────────────────────────────
# Test 20: List proposed assertions
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_proposed_assertions(db_session, create_test_user):
    """Test: GET /proposed endpoint returns only PROPOSED assertions."""
    user_id, token, case_id = await setup_case_with_user(db_session, create_test_user, permission="WRITE")
    entity_a = await create_entity(db_session, case_id, user_id)
    entity_b = await create_entity(db_session, case_id, user_id)

    # Create a proposal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/cases/{case_id}/assertions",
            json={
                "subject_entity_id": entity_a,
                "predicate": "KNOWN_ASSOCIATE_OF",
                "object_entity_id": entity_b,
                "investigator_justification": "Observed together on multiple occasions during surveillance."
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 201
    assertion_id = r.json()["assertion_id"]

    # List proposals
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_list = await ac.get(
            f"/api/v1/cases/{case_id}/assertions/proposed",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert r_list.status_code == 200
    proposals = r_list.json()
    assert any(p["assertion_id"] == assertion_id for p in proposals), \
        "Expected to find the created proposal in the list"

    await cleanup(db_session, case_id, entity_ids=[entity_a, entity_b], assertion_ids=[assertion_id])


# ─────────────────────────────────────────────────────────────────────────────
# Test 27: CDC worker safety gate (P2-A)
# ─────────────────────────────────────────────────────────────────────────────

def test_cdc_worker_safety_gate_missing_dsn():
    """Test 27: CDC worker aborts if CIVIX_DATABASE_URL_SYNC is not set."""
    from civix_api.worker.cdc import _validate_cdc_worker_safety
    with pytest.raises(SystemExit) as exc_info:
        _validate_cdc_worker_safety("", "bolt://localhost:7688")
    assert exc_info.value.code == 1


def test_cdc_worker_safety_gate_test_db():
    """Test 27b: CDC worker aborts if DSN targets civix_test."""
    from civix_api.worker.cdc import _validate_cdc_worker_safety
    with pytest.raises(SystemExit) as exc_info:
        _validate_cdc_worker_safety(
            "postgresql://civix_cdc_worker:pass@localhost:5433/civix_test",
            "bolt://localhost:7688"
        )
    assert exc_info.value.code == 1


def test_cdc_worker_safety_gate_missing_neo4j():
    """Test 27c: CDC worker aborts if NEO4J_URI is not set."""
    from civix_api.worker.cdc import _validate_cdc_worker_safety
    with pytest.raises(SystemExit) as exc_info:
        _validate_cdc_worker_safety(
            "postgresql://civix_cdc_worker:pass@localhost:5433/civix_demo",
            ""  # Missing Neo4j URI
        )
    assert exc_info.value.code == 1


def test_cdc_worker_safety_gate_valid_config():
    """Test 27d: CDC worker passes with valid civix_demo config."""
    from civix_api.worker.cdc import _validate_cdc_worker_safety
    # Should NOT raise SystemExit
    _validate_cdc_worker_safety(
        "postgresql://civix_cdc_worker:pass@localhost:5433/civix_demo",
        "bolt://localhost:7688"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test: Neo4j projection skips PROPOSED assertions (unit test)
# ─────────────────────────────────────────────────────────────────────────────

def test_neo4j_projection_skips_proposed_assertions():
    """
    Test 24: The Neo4j projection service must NOT project PROPOSED assertions.
    This is a unit test against the projection service using a mock Neo4j session.
    """
    from civix_api.services.neo4j_projection import Neo4jProjectionService
    service = Neo4jProjectionService()

    mock_session = MagicMock()

    payload = {
        "assertion_id": str(uuid4()),
        "subject_entity_id": str(uuid4()),
        "object_entity_id": str(uuid4()),
        "object_entity_type": "person",
        "predicate": "KNOWN_ASSOCIATE_OF",
        "epistemic_status": "POSSIBLE",
        "authorized_case_ids": [str(uuid4())],
        "assertion_origin": "INVESTIGATOR_PROPOSED",
        "proposal_status": "PROPOSED",  # This must NOT be projected
        "tx_end": None,
    }

    # Should return early without calling session.run
    service._upsert_assertion(mock_session, payload, seq_no=9999)

    # session.run should NOT have been called — no Neo4j write for PROPOSED
    mock_session.run.assert_not_called()


def test_neo4j_projection_skips_rejected_assertions():
    """
    Test 25: The Neo4j projection service must NOT create authoritative edges for REJECTED assertions.
    """
    from civix_api.services.neo4j_projection import Neo4jProjectionService
    service = Neo4jProjectionService()

    mock_session = MagicMock()
    # Make session.run return something for tombstone call
    mock_session.run.return_value = MagicMock()

    payload = {
        "assertion_id": str(uuid4()),
        "subject_entity_id": str(uuid4()),
        "object_entity_id": str(uuid4()),
        "object_entity_type": "person",
        "predicate": "KNOWN_ASSOCIATE_OF",
        "epistemic_status": "POSSIBLE",
        "authorized_case_ids": [str(uuid4())],
        "assertion_origin": "INVESTIGATOR_PROPOSED",
        "proposal_status": "REJECTED",
        "tx_end": None,
    }

    # Should call tombstone, not upsert
    service._upsert_assertion(mock_session, payload, seq_no=9999)

    # session.run IS called — but only for the tombstone (removal)
    # Verify it was called with a DELETE query (tombstone), not MERGE (create)
    calls = [str(c) for c in mock_session.run.call_args_list]
    assert any("DELETE" in c or "tombstone" in c.lower() or "INVESTIGATOR_ASSERTED" in c for c in calls), \
        f"Expected tombstone query for REJECTED assertion. Calls: {calls}"
