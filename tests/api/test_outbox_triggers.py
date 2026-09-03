import pytest
import asyncio
from sqlalchemy import text
from uuid import uuid4

@pytest.mark.asyncio
async def test_person_upsert_outbox_trigger(db_session, create_test_user):
    user_id = await create_test_user()
    entity_id = uuid4()
    
    # Simulate application creating a person
    await db_session.execute(
        text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"),
        {"uid": str(user_id)}
    )
    
    # 1. Insert entity
    await db_session.execute(
        text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:eid, 'PERSON', :uid)"),
        {"eid": entity_id, "uid": user_id}
    )
    
    # 2. Insert person
    await db_session.execute(
        text("INSERT INTO civix.person (entity_id, display_name, gender) VALUES (:eid, 'John Doe', 'MALE')"),
        {"eid": entity_id}
    )
    
    # Commit the transaction so outbox trigger completes
    await db_session.commit()
    
    # 3. Check outbox
    result = await db_session.execute(
        text("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = :eid"),
        {"eid": entity_id}
    )
    events = result.fetchall()
    
    assert len(events) == 1
    event = events[0]
    
    assert event.action == 'UPSERT_NODE'
    assert event.entity_type == 'person'
    assert event.payload['display_name'] == 'John Doe'
    assert event.payload['gender'] == 'MALE'
    assert 'notes' not in event.payload or event.payload['notes'] is None

    # 4. Update person
    await db_session.execute(
        text("UPDATE civix.person SET display_name = 'Johnathan Doe' WHERE entity_id = :eid"),
        {"eid": entity_id}
    )
    await db_session.commit()
    
    # 5. Check outbox for second event
    result = await db_session.execute(
        text("SELECT action, payload FROM civix.outbox WHERE entity_id = :eid ORDER BY created_at ASC"),
        {"eid": entity_id}
    )
    events = result.fetchall()
    
    assert len(events) == 2
    assert events[1].action == 'UPSERT_NODE'
    assert events[1].payload['display_name'] == 'Johnathan Doe'

@pytest.mark.asyncio
async def test_case_upsert_outbox_trigger(db_session, create_test_user):
    user_id = await create_test_user()
    case_id = uuid4()
    
    # Simulate application creating a case (required for RLS)
    await db_session.execute(
        text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"),
        {"uid": str(user_id)}
    )
    
    # 1. Insert case_access first (FK is deferred, but required by RLS WITH CHECK)
    await db_session.execute(
        text("INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES (:cid, :uid, 'ADMIN', :uid)"),
        {"cid": case_id, "uid": str(user_id)}
    )
    
    # 2. Insert investigative case
    case_number = f"CIV-{uuid4().hex[:8]}"
    await db_session.execute(
        text(f"INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at) VALUES (:cid, '{case_number}', 'Test Case', 'FINANCIAL', 'Delhi', now())"),
        {"cid": case_id}
    )
    await db_session.commit()
    
    # Check outbox
    result = await db_session.execute(
        text("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = :cid"),
        {"cid": case_id}
    )
    events = result.fetchall()
    
    assert len(events) == 1
    event = events[0]
    
    assert event.action == 'UPSERT_NODE'
    assert event.entity_type == 'investigative_case'
    assert event.payload['case_number'] == case_number
    assert event.payload['title'] == 'Test Case'

@pytest.mark.asyncio
async def test_event_upsert_outbox_trigger(db_session, create_test_user):
    user_id = await create_test_user()
    event_id = uuid4()
    
    await db_session.execute(
        text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"),
        {"uid": str(user_id)}
    )
    
    await db_session.execute(
        text("INSERT INTO civix.event (event_id, event_type, occurred_at, description) VALUES (:eid, 'SURVEILLANCE_OBSERVATION', '[2026-08-01 10:00, 2026-08-01 12:00)'::tstzrange, 'Test Event')"),
        {"eid": event_id}
    )
    await db_session.commit()
    
    result = await db_session.execute(
        text("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = :eid"),
        {"eid": event_id}
    )
    events = result.fetchall()
    
    assert len(events) == 1
    event = events[0]
    
    assert event.action == 'UPSERT_NODE'
    assert event.entity_type == 'event'
    assert event.payload['event_type'] == 'SURVEILLANCE_OBSERVATION'
    assert event.payload['description'] == 'Test Event'

@pytest.mark.asyncio
async def test_assertion_upsert_outbox_trigger(db_session, create_test_user):
    user_id = await create_test_user()
    case_id = uuid4()
    assertion_id = uuid4()
    person_id = uuid4()
    identity_id = uuid4()
    
    await db_session.execute(
        text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"),
        {"uid": str(user_id)}
    )
    
    await db_session.execute(
        text("INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES (:cid, :uid, 'ADMIN', :uid)"),
        {"cid": case_id, "uid": str(user_id)}
    )
    case_number = f"CIV-{uuid4().hex[:8]}"
    await db_session.execute(
        text(f"INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at) VALUES (:cid, '{case_number}', 'Test Case', 'FINANCIAL', 'Delhi', now())"),
        {"cid": case_id}
    )

    await db_session.execute(
        text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:eid, 'PERSON', :uid)"),
        {"eid": person_id, "uid": user_id}
    )
    await db_session.execute(
        text("INSERT INTO civix.person (entity_id, display_name, gender) VALUES (:eid, 'John Doe', 'MALE')"),
        {"eid": person_id}
    )

    await db_session.execute(
        text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:eid, 'SOURCE_IDENTITY', :uid)"),
        {"eid": identity_id, "uid": user_id}
    )
    await db_session.execute(
        text("INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at) VALUES (:eid, 'Agent 47', 'NAME', '2026-08-01 10:00:00+00')"),
        {"eid": identity_id}
    )
    
    await db_session.execute(
        text("INSERT INTO civix.assertion (assertion_id, predicate, epistemic_status, subject_entity_id, object_entity_id, asserted_by) VALUES (:aid, 'SEEN_AT', 'CONFIRMED', :sid, :oid, :uid)"),
        {"aid": assertion_id, "sid": identity_id, "oid": person_id, "uid": str(user_id)}
    )
    
    await db_session.commit()
    
    result = await db_session.execute(
        text("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = :aid"),
        {"aid": assertion_id}
    )
    events = result.fetchall()
    
    assert len(events) == 1
    event = events[0]
    
    assert event.action == 'UPSERT_NODE'
    assert event.entity_type == 'assertion'
    assert event.payload['predicate'] == 'SEEN_AT'
    assert event.payload['object_entity_type'] == 'PERSON'

