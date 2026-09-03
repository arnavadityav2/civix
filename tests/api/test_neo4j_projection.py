import pytest
import uuid
from unittest.mock import MagicMock
from civix_api.services.neo4j_projection import Neo4jProjectionService

@pytest.fixture
def projection_service():
    return Neo4jProjectionService()

@pytest.fixture
def mock_session():
    return MagicMock()

def test_person_entity_id(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id, "primary_name": "Test Person"}
    
    projection_service.project(mock_session, "UPSERT_NODE", "person", payload, seq_no=100)
    
    call_args = mock_session.run.call_args
    query, kwargs = call_args[0][0], call_args[1]
    
    assert "MERGE (n:Person {entity_id: $ident_val})" in query
    assert kwargs['ident_val'] == entity_id
    assert kwargs['seq_no'] == 100
    assert "SET n._lock = true" in query
    assert "last_seq_no = $seq_no" in query

def test_device_entity_id(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id, "imei": "1234567890"}
    
    projection_service.project(mock_session, "UPSERT_NODE", "device", payload, seq_no=101)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (n:Device {entity_id: $ident_val})" in query
    assert kwargs['ident_val'] == entity_id

def test_property_entity_id(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id, "property_ref": "REF-001"}
    
    projection_service.project(mock_session, "UPSERT_NODE", "property", payload, seq_no=102)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (n:Property {entity_id: $ident_val})" in query
    assert kwargs['ident_val'] == entity_id

def test_case_case_id(projection_service, mock_session):
    case_id = str(uuid.uuid4())
    payload = {"case_id": case_id, "case_number": "CASE-123"}
    
    projection_service.project(mock_session, "UPSERT_NODE", "investigative_case", payload, seq_no=103)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (n:Case {case_id: $ident_val})" in query
    assert kwargs['ident_val'] == case_id

def test_fir_fir_id(projection_service, mock_session):
    fir_id = str(uuid.uuid4())
    payload = {"fir_id": fir_id, "fir_number": "FIR-456"}
    
    projection_service.project(mock_session, "UPSERT_NODE", "fir", payload, seq_no=104)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (n:FIR {fir_id: $ident_val})" in query
    assert kwargs['ident_val'] == fir_id

def test_tombstone_person(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id, "tombstoned_at": "2026-08-30"}
    
    projection_service.project(mock_session, "TOMBSTONE_NODE", "person", payload, seq_no=105)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MATCH (n:Person {entity_id: $ident_val})" in query
    assert "SET n._lock = true" in query
    assert "SET n.visibility_status = 'TOMBSTONED'" in query
    assert kwargs['ident_val'] == entity_id

def test_tombstone_case(projection_service, mock_session):
    case_id = str(uuid.uuid4())
    payload = {"case_id": case_id, "tombstoned_at": "2026-08-30"}
    
    projection_service.project(mock_session, "TOMBSTONE_NODE", "investigative_case", payload, seq_no=106)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MATCH (n:Case {case_id: $ident_val})" in query
    assert "SET n._lock = true" in query
    assert "SET n.visibility_status = 'TOMBSTONED'" in query
    assert kwargs['ident_val'] == case_id

def test_stale_seq_no_guard(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id}
    
    projection_service.project(mock_session, "UPSERT_NODE", "person", payload, seq_no=99)
    
    query, _ = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    # The Cypher query itself protects against stale replays
    assert "WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply" in query
    assert "last_seq_no = $seq_no" in query

def test_duplicate_replayed_events_guard(projection_service, mock_session):
    entity_id = str(uuid.uuid4())
    payload = {"entity_id": entity_id}
    
    projection_service.project(mock_session, "DEACTIVATE_NODE", "person", payload, seq_no=50)
    
    query, _ = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply" in query

def test_edge_idempotency(projection_service, mock_session):
    support_id = str(uuid.uuid4())
    payload = {
        "support_id": support_id,
        "hypothesis_id": str(uuid.uuid4()),
        "assertion_id": str(uuid.uuid4())
    }
    
    projection_service.project(mock_session, "UPSERT_NODE", "hypothesis_support", payload, seq_no=200)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (a)-[r:HAS_STANCE {support_id: $support_id}]->(h)" in query
    assert "SET r._lock = true" in query
    assert "WITH r, (r.last_seq_no IS NULL OR $seq_no > r.last_seq_no) AS should_apply" in query
    assert "r.last_seq_no = $seq_no" in query
    assert kwargs['seq_no'] == 200

def test_missing_identity_raises(projection_service, mock_session):
    payload = {"name": "No ID"}
    with pytest.raises(ValueError, match="Missing identity for person"):
        projection_service.project(mock_session, "UPSERT_NODE", "person", payload, seq_no=1)

def test_missing_support_id_raises(projection_service, mock_session):
    payload = {"hypothesis_id": "123"} # missing support_id
    with pytest.raises(ValueError, match="Missing identifiers for hypothesis_support"):
        projection_service.project(mock_session, "UPSERT_NODE", "hypothesis_support", payload, seq_no=1)

def test_investigative_lead_authorized_properties(projection_service, mock_session):
    lead_id = str(uuid.uuid4())
    case_id = str(uuid.uuid4())
    payload = {
        "lead_id": lead_id,
        "case_id": case_id,
        "priority": "HIGH",
        "status": "OPEN",
        "target_entity_id": str(uuid.uuid4()), # Should NOT be projected
        "hypothesis_id": str(uuid.uuid4()),    # Should NOT be projected
        "lead_text": "Secret tip",             # Should NOT be projected
        "ai_confidence": 0.95                  # Should NOT be projected
    }
    
    projection_service.project(mock_session, "UPSERT_NODE", "investigative_lead", payload, seq_no=150)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "MERGE (n:Lead {lead_id: $lead_id})" in query
    assert kwargs['lead_id'] == lead_id
    
    auth_payload = kwargs['authorized_payload']
    assert auth_payload['lead_id'] == lead_id
    assert auth_payload['case_id'] == case_id
    assert auth_payload['priority'] == "HIGH"
    assert auth_payload['status'] == "OPEN"
    assert "target_entity_id" not in auth_payload
    assert "hypothesis_id" not in auth_payload
    assert "lead_text" not in auth_payload
    assert "ai_confidence" not in auth_payload

def test_investigative_lead_closed_status_deletes(projection_service, mock_session):
    lead_id = str(uuid.uuid4())
    payload = {
        "lead_id": lead_id,
        "status": "CLOSED"
    }
    
    projection_service.project(mock_session, "UPSERT_NODE", "investigative_lead", payload, seq_no=151)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "DETACH DELETE n" in query
    assert kwargs['lead_id'] == lead_id

def test_investigative_lead_false_positive_status_deletes(projection_service, mock_session):
    lead_id = str(uuid.uuid4())
    payload = {
        "lead_id": lead_id,
        "status": "FALSE_POSITIVE"
    }
    
    projection_service.project(mock_session, "UPSERT_NODE", "investigative_lead", payload, seq_no=152)
    
    query, kwargs = mock_session.run.call_args[0][0], mock_session.run.call_args[1]
    assert "DETACH DELETE n" in query
    assert kwargs['lead_id'] == lead_id
