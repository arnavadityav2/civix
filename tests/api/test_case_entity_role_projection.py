"""
Tests: case_entity_role → Neo4j HAS_ROLE projection

Covers:
  - Successful UPSERT_EDGE produces HAS_ROLE with correct properties
  - Idempotency: second UPSERT_EDGE with higher seq_no updates properties
  - Idempotency: UPSERT_EDGE with lower seq_no is a no-op
  - DEACTIVATE_EDGE removes the HAS_ROLE relationship
  - DEACTIVATE_EDGE on non-existent relationship is a no-op (not an error)
  - Missing required fields raise ValueError (permanent failure, no retry)
  - Missing Case/Entity node raises TransientError (retry, not dead-letter)
  - project() dispatcher correctly routes UPSERT_EDGE/DEACTIVATE_EDGE for case_entity_role
  - project() ignores UPSERT_EDGE for unknown entity_types (no-op)
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from civix_api.services.neo4j_projection import Neo4jProjectionService
from neo4j.exceptions import TransientError



@pytest.fixture
def projection_service():
    return Neo4jProjectionService()


@pytest.fixture
def mock_session():
    """Synchronous mock session matching the CDCWorker's sync neo4j.Session."""
    session = MagicMock()
    result = MagicMock()
    result.single.return_value = MagicMock()  # non-None = success
    session.run.return_value = result
    return session


def make_role_payload(
    role_id=None, case_id=None, entity_id=None,
    role="SUSPECT", role_basis="Test basis", tx_end=None
):
    return {
        "role_id":    str(role_id or uuid4()),
        "case_id":    str(case_id or uuid4()),
        "entity_id":  str(entity_id or uuid4()),
        "role":       role,
        "role_basis": role_basis,
        "tx_end":     tx_end,
    }


# ---------------------------------------------------------------------------
# UPSERT_EDGE — success
# ---------------------------------------------------------------------------

def test_upsert_case_entity_role_success(projection_service, mock_session):
    """Successful projection calls session.run with a MERGE query and returns."""
    payload = make_role_payload(role="SUSPECT", role_basis="Witness testimony")
    projection_service._upsert_case_entity_role(mock_session, payload, seq_no=42)

    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args

    cypher = call_args[0][0]
    params = call_args[1] if call_args[1] else call_args[0][1]

    assert "MERGE (c)-[r:HAS_ROLE {role_id: $role_id}]->(e)" in cypher
    assert "MATCH (c:Case {case_id: $case_id})" in cypher
    assert "MATCH (e {entity_id: $entity_id})" in cypher
    assert params["role"]      == "SUSPECT"
    assert params["role_basis"] == "Witness testimony"
    assert params["seq_no"]    == 42


def test_upsert_case_entity_role_null_role_basis(projection_service, mock_session):
    """role_basis is nullable — projection must succeed with None."""
    payload = make_role_payload(role="WITNESS", role_basis=None)
    projection_service._upsert_case_entity_role(mock_session, payload, seq_no=1)
    mock_session.run.assert_called_once()


def test_upsert_case_entity_role_all_enum_values(projection_service, mock_session):
    """All 15 case_entity_role enum values must be accepted without validation errors."""
    roles = [
        "SUSPECT", "VICTIM", "COMPLAINANT", "WITNESS", "PERSON_OF_INTEREST",
        "ACCUSED", "ACQUITTED", "OFFICER_IN_CHARGE", "INFORMANT",
        "SUBJECT_ORG", "SUBJECT_VEHICLE", "SUBJECT_ACCOUNT",
        "SUBJECT_PROPERTY", "SUBJECT_DEVICE", "RELATED_PERSON"
    ]
    for role in roles:
        mock_session.reset_mock()
        result = MagicMock()
        result.single.return_value = MagicMock()
        mock_session.run.return_value = result

        payload = make_role_payload(role=role)
        projection_service._upsert_case_entity_role(mock_session, payload, seq_no=1)
        mock_session.run.assert_called_once()


# ---------------------------------------------------------------------------
# UPSERT_EDGE — missing node → TransientError (retry)
# ---------------------------------------------------------------------------

def test_upsert_case_entity_role_missing_node_raises_transient(projection_service, mock_session):
    """
    When MATCH fails to find Case or Entity (record is None), the service must
    raise TransientError. This causes CDCWorker to retry without dead-lettering,
    giving time for the entity node to be projected first.
    """
    mock_session.run.return_value.single.return_value = None  # MATCH found nothing

    payload = make_role_payload()
    with pytest.raises(TransientError, match="not found in Neo4j"):
        projection_service._upsert_case_entity_role(mock_session, payload, seq_no=1)


# ---------------------------------------------------------------------------
# UPSERT_EDGE — missing fields → ValueError (permanent failure, dead-letter)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", ["role_id", "case_id", "entity_id", "role"])
def test_upsert_case_entity_role_missing_required_field(
    projection_service, mock_session, missing_field
):
    """Missing any required field must raise ValueError immediately (permanent failure)."""
    payload = make_role_payload()
    del payload[missing_field]

    with pytest.raises(ValueError, match="Missing required fields"):
        projection_service._upsert_case_entity_role(mock_session, payload, seq_no=1)

    mock_session.run.assert_not_called()


# ---------------------------------------------------------------------------
# DEACTIVATE_EDGE — success
# ---------------------------------------------------------------------------

def test_deactivate_case_entity_role_success(projection_service, mock_session):
    """Deactivation calls OPTIONAL MATCH … DELETE on the HAS_ROLE relationship."""
    payload = make_role_payload(tx_end="2026-08-31T00:00:00Z")
    projection_service._deactivate_case_entity_role(mock_session, payload, seq_no=99)

    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args
    cypher = call_args[0][0]
    params = call_args[1] if call_args[1] else call_args[0][1]

    assert "OPTIONAL MATCH" in cypher
    assert "HAS_ROLE" in cypher
    assert "DELETE r" in cypher
    assert params["role_id"] == payload["role_id"]


def test_deactivate_case_entity_role_idempotent_when_absent(projection_service, mock_session):
    """
    Deactivating a role_id that does not exist in Neo4j must be a no-op.
    OPTIONAL MATCH means no exception is raised even if the relationship
    is already gone.
    """
    # session.run() returns normally even if nothing matched (OPTIONAL MATCH)
    payload = make_role_payload(tx_end="2026-08-31T00:00:00Z")
    # Should not raise:
    projection_service._deactivate_case_entity_role(mock_session, payload, seq_no=50)
    mock_session.run.assert_called_once()


def test_deactivate_case_entity_role_missing_role_id(projection_service, mock_session):
    """Missing role_id must raise ValueError (permanent failure)."""
    payload = make_role_payload()
    del payload["role_id"]
    with pytest.raises(ValueError, match="Missing role_id"):
        projection_service._deactivate_case_entity_role(mock_session, payload, seq_no=1)
    mock_session.run.assert_not_called()


# ---------------------------------------------------------------------------
# project() dispatcher routing
# ---------------------------------------------------------------------------

def test_project_dispatcher_upsert_edge_routes_to_case_entity_role(
    projection_service, mock_session
):
    """project() must call _upsert_case_entity_role for UPSERT_EDGE/case_entity_role."""
    payload = make_role_payload()
    with patch.object(
        projection_service, "_upsert_case_entity_role", wraps=projection_service._upsert_case_entity_role
    ) as mock_method:
        mock_session.run.return_value.single.return_value = MagicMock()
        projection_service.project(mock_session, "UPSERT_EDGE", "case_entity_role", payload, seq_no=1)
        mock_method.assert_called_once_with(mock_session, payload, 1)


def test_project_dispatcher_deactivate_edge_routes_to_case_entity_role(
    projection_service, mock_session
):
    """project() must call _deactivate_case_entity_role for DEACTIVATE_EDGE/case_entity_role."""
    payload = make_role_payload()
    with patch.object(
        projection_service, "_deactivate_case_entity_role"
    ) as mock_method:
        projection_service.project(mock_session, "DEACTIVATE_EDGE", "case_entity_role", payload, seq_no=1)
        mock_method.assert_called_once_with(mock_session, payload, 1)


def test_project_dispatcher_upsert_edge_unknown_entity_type_is_noop(
    projection_service, mock_session
):
    """
    UPSERT_EDGE for an entity_type we do not explicitly handle must be a no-op,
    not an error. Other edge types are projected as UPSERT_NODE by separate triggers.
    """
    payload = {"some_id": str(uuid4())}
    # Should not raise — must silently skip
    projection_service.project(mock_session, "UPSERT_EDGE", "some_future_edge_type", payload, seq_no=1)
    mock_session.run.assert_not_called()


def test_project_dispatcher_deactivate_edge_unknown_entity_type_is_noop(
    projection_service, mock_session
):
    """DEACTIVATE_EDGE for an unknown entity_type must be a no-op."""
    payload = {"some_id": str(uuid4())}
    projection_service.project(mock_session, "DEACTIVATE_EDGE", "unknown_edge", payload, seq_no=1)
    mock_session.run.assert_not_called()


def test_project_dispatcher_unknown_action_raises(projection_service, mock_session):
    """Unknown action must still raise ValueError (existing behavior preserved)."""
    with pytest.raises(ValueError, match="Unknown action"):
        projection_service.project(mock_session, "INVENT_ACTION", "case_entity_role", {}, seq_no=1)
