import pytest
import psycopg2
import uuid
import json
from civix_api.worker.cdc import CDCWorker
from unittest.mock import patch, MagicMock
from neo4j.exceptions import TransientError, ClientError

DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

@pytest.fixture(scope="module")
def worker():
    return CDCWorker(DSN, "bolt://localhost:7687", "neo4j", "password")

@pytest.fixture(autouse=True)
def clean_db():
    # Setup test sequence
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM civix.outbox WHERE action LIKE 'TEST_%'")
            conn.commit()

def insert_test_event(entity_id=None, action="TEST_EVENT", payload={}):
    if not entity_id:
        entity_id = uuid.uuid4()
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
                VALUES (%s, %s, 'TEST', %s) RETURNING id
            """, (str(entity_id), action, json.dumps(payload)))
            conn.commit()
            return cur.fetchone()[0]

def get_event_state(event_id):
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT consumed_at, error_status, retry_count FROM civix.outbox WHERE id = %s", (str(event_id),))
            return cur.fetchone()

# TEST-01 Successful event
def test_successful_event(worker):
    event_id = insert_test_event()
    with patch.object(worker.projection_service, 'project', return_value=True):
        assert worker.process_next_event() is True
    state = get_event_state(event_id)
    assert state[0] is not None  # consumed_at
    assert state[1] is None      # error_status
    assert state[2] == 0         # retry_count

# TEST-02 Transient failure followed by success
def test_transient_failure_then_success(worker):
    event_id = insert_test_event()
    
    # 1. Transient failure
    with patch.object(worker.projection_service, 'project', side_effect=TransientError("Network glitch")):
        assert worker.process_next_event() is True
    
    state = get_event_state(event_id)
    assert state[0] is None      # consumed_at
    assert state[1] is None      # error_status
    assert state[2] == 1         # retry_count
    
    # 2. Success
    with patch.object(worker.projection_service, 'project', return_value=True):
        assert worker.process_next_event() is True
        
    state = get_event_state(event_id)
    assert state[0] is not None
    assert state[1] is None
    assert state[2] == 1

# TEST-03 Permanent failure after exactly 3 attempts
def test_permanent_failure_3_attempts(worker):
    event_id = insert_test_event()
    
    with patch.object(worker.projection_service, 'project', side_effect=ValueError("Poison")):
        # Attempt 1
        assert worker.process_next_event() is True
        print(f"State 1: {get_event_state(event_id)}")
        
        # Attempt 2
        assert worker.process_next_event() is True
        print(f"State 2: {get_event_state(event_id)}")
        
        # Attempt 3 -> Permanent Failure
        assert worker.process_next_event() is True
        state = get_event_state(event_id)
        print(f"State 3: {state}")
        
        assert state[0] is None
        assert state[1] == 'PERMANENT_FAILURE'
        assert state[2] == 3

# TEST-07 Poison event does not block later valid event
# TEST-08 Same-entity ordering behavior
def test_poison_event_does_not_block_later_event(worker):
    entity_id = uuid.uuid4()
    event_a_id = insert_test_event(entity_id, "TEST_A")
    event_b_poison_id = insert_test_event(entity_id, "TEST_B")
    event_c_id = insert_test_event(entity_id, "TEST_C")
    
    processed = []
    def mock_project(session, action, *args):
        if action == "TEST_B":
            raise ValueError("Poison")
        processed.append(action)
        return True

    with patch.object(worker.projection_service, 'project', side_effect=mock_project):
        # 1. Event A processed successfully
        assert worker.process_next_event() is True
        assert processed == ["TEST_A"]
        
        # 2. Event B fails (attempt 1)
        assert worker.process_next_event() is True
        # 3. Event B fails (attempt 2)
        assert worker.process_next_event() is True
        # 4. Event B fails (attempt 3) -> Permanent Failure
        assert worker.process_next_event() is True
        
        # 5. Event C processed successfully
        assert worker.process_next_event() is True
        assert processed == ["TEST_A", "TEST_C"]
        
        state_b = get_event_state(event_b_poison_id)
        assert state_b[1] == 'PERMANENT_FAILURE'
        
        state_c = get_event_state(event_c_id)
        assert state_c[0] is not None

# TEST-10 Worker continuation after permanent failure
def test_worker_continuation():
    # Same as TEST-07, already verified worker continues naturally.
    pass

