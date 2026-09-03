import pytest
import psycopg
import uuid
import os
from unittest.mock import MagicMock
from civix_api.worker.cdc import CDCWorker
from neo4j.exceptions import ClientError, TransientError

@pytest.fixture
def mock_neo4j():
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    return driver, session

@pytest.fixture
def db_conn():
    dsn = "postgresql://postgres:postgres@localhost:5433/civix_test"
    conn = psycopg.connect(dsn, autocommit=True)
    yield conn
    conn.close()

@pytest.fixture
def worker(mock_neo4j):
    driver, _ = mock_neo4j
    # Override driver creation
    worker = CDCWorker("postgresql://postgres:postgres@localhost:5433/civix_test", "bolt://dummy", "dummy", "dummy")
    worker.neo4j_driver = driver
    return worker

def test_successful_consumption(worker, db_conn, mock_neo4j):
    _, session = mock_neo4j
    
    # 1. Setup outbox event
    entity_id = str(uuid.uuid4())
    db_conn.execute("DELETE FROM civix.outbox")
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id, "UPSERT_NODE", "person", f'{{"entity_id": "{entity_id}", "name": "John"}}')
    )
    
    # 2. Run worker
    processed = worker.process_next_event()
    
    # 3. Verify Neo4j was called
    assert processed is True
    session.run.assert_called_once()
    
    # 4. Verify consumed_at is set
    cur = db_conn.execute("SELECT consumed_at, error_status FROM civix.outbox WHERE entity_id = %s", (entity_id,))
    row = cur.fetchone()
    assert row[0] is not None # consumed_at
    assert row[1] is None     # error_status

def test_transient_failure(worker, db_conn, mock_neo4j):
    _, session = mock_neo4j
    session.run.side_effect = TransientError("Connection lost")
    
    entity_id = str(uuid.uuid4())
    db_conn.execute("DELETE FROM civix.outbox")
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id, "UPSERT_NODE", "person", f'{{"entity_id": "{entity_id}"}}')
    )
    
    processed = worker.process_next_event()
    assert processed is True
    
    cur = db_conn.execute("SELECT consumed_at, error_status FROM civix.outbox WHERE entity_id = %s", (entity_id,))
    row = cur.fetchone()
    assert row[0] is None # consumed_at
    assert row[1] is None # error_status, event remains pending

def test_permanent_failure_blocking(worker, db_conn, mock_neo4j):
    _, session = mock_neo4j
    # We mock ClientError for Neo4j syntax error / constraint violation
    session.run.side_effect = ClientError("Invalid syntax")
    
    entity_id = str(uuid.uuid4())
    entity_id_2 = str(uuid.uuid4())
    db_conn.execute("DELETE FROM civix.outbox")
    
    # Event 1 for Entity X (will fail)
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id, "UPSERT_NODE", "person", f'{{"entity_id": "{entity_id}"}}')
    )
    # Event 2 for Entity X (should be blocked)
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id, "DEACTIVATE_NODE", "person", f'{{"entity_id": "{entity_id}"}}')
    )
    # Event 3 for Entity Y (should be processable)
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id_2, "UPSERT_NODE", "person", f'{{"entity_id": "{entity_id_2}"}}')
    )
    
    # 1. Process Event 1 -> Permanent Failure
    worker.process_next_event()
    
    cur = db_conn.execute("SELECT error_status FROM civix.outbox WHERE action='UPSERT_NODE' AND entity_id = %s", (entity_id,))
    assert cur.fetchone()[0] == 'PERMANENT_FAILURE'
    
    # 2. Process next event -> Should be Event 3 for Entity Y (since Entity X is blocked)
    # Reset mock to succeed
    session.run.side_effect = None
    worker.process_next_event()
    
    # Verify Event 3 is consumed
    cur = db_conn.execute("SELECT consumed_at FROM civix.outbox WHERE entity_id = %s", (entity_id_2,))
    assert cur.fetchone()[0] is not None
    
    # Verify Event 2 is still pending
    cur = db_conn.execute("SELECT consumed_at, error_status FROM civix.outbox WHERE action='DEACTIVATE_NODE' AND entity_id = %s", (entity_id,))
    row = cur.fetchone()
    assert row[0] is None
    assert row[1] is None

def test_tombstone_identity(worker, db_conn, mock_neo4j):
    _, session = mock_neo4j
    
    case_id = str(uuid.uuid4())
    db_conn.execute("DELETE FROM civix.outbox")
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (case_id, "TOMBSTONE_NODE", "investigative_case", f'{{"case_id": "{case_id}", "tombstoned_at": "2026-08-30"}}')
    )
    
    worker.process_next_event()
    
    # Check that Neo4j was called with case_id identifier
    call_args = session.run.call_args
    assert call_args is not None
    query, kwargs = call_args[0][0], call_args[1]
    assert "MATCH (n:Case {case_id: $ident_val})" in query
    assert kwargs['ident_val'] == case_id

def test_stale_replay_guard(worker, db_conn, mock_neo4j):
    _, session = mock_neo4j
    # Since we mock Neo4j, we just verify the Cypher query contains the seq_no guard
    entity_id = str(uuid.uuid4())
    db_conn.execute("DELETE FROM civix.outbox")
    db_conn.execute(
        "INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, %s, %s, %s)",
        (entity_id, "UPSERT_NODE", "person", f'{{"entity_id": "{entity_id}"}}')
    )
    
    worker.process_next_event()
    call_args = session.run.call_args
    query = call_args[0][0]
    
    assert "WITH n, (n.last_seq_no IS NULL OR $seq_no > n.last_seq_no) AS should_apply" in query
    assert "last_seq_no = $seq_no" in query
