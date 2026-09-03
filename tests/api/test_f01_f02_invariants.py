import pytest
import asyncio
from sqlalchemy import text
from httpx import AsyncClient
import uuid
import jwt
from datetime import datetime, timedelta
from civix_api.config import settings

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.fixture
async def setup_ingest_data(db_session, create_test_user):
    user_investigator = await create_test_user()
    token_investigator = create_token(sub=str(user_investigator))
    
    case_id = uuid.uuid4()
    source_id = uuid.uuid4()
    
    # Temporarily bypass RLS
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_investigator)})
    
    # 1. Create Source
    await db_session.execute(
        text("INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score) VALUES (:sid, :sname, 'TELECOM', 0.9)"),
        {"sid": source_id, "sname": f"Test Telecom {source_id}"}
    )
    
    # 2. Grant case access
    await db_session.execute(
        text("INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by) VALUES (:a1, :cid, :uid_write, 'WRITE', :uid_write)"),
        {"a1": uuid.uuid4(), "cid": case_id, "uid_write": user_investigator}
    )
    
    # 3. Create Case
    await db_session.execute(
        text("INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at) VALUES (:cid, :cnum, 'Test Ingest Case', 'CRIMINAL', 'Test', CURRENT_DATE)"),
        {"cid": case_id, "cnum": f"CIV-2026-ING-{str(case_id)[:6]}"}
    )
    
    await db_session.commit()
    await db_session.execute(text("SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"))
    
    return {
        "case_id": case_id,
        "source_id": source_id,
        "token_investigator": token_investigator
    }

@pytest.mark.asyncio
async def test_f01_ingestion_idempotency_null_bypass(
    client: AsyncClient, 
    db_session, 
    setup_ingest_data
):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    # 1. Attempt to ingest a payload without an external_reference
    payload = {
        "source_id": str(source_id),
        "records": [
            {
                "timestamp": "2026-08-01T12:00:00Z",
                "caller_identifier": "+15550000001",
                "callee_identifier": "+15550000002",
                "duration_seconds": 60,
                "call_type": "VOICE",
                "external_reference": None,
                "cell_tower_start": None,
                "cell_tower_end": None,
                "imei": None,
                "imsi": None
            }
        ]
    }
    
    # First ingest should succeed
    res1 = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr", 
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res1.status_code == 200, f"res1 failed: {res1.text}"
    data1 = res1.json()
    assert data1["accepted_count"] == 1
    assert data1["duplicate_count"] == 0
    
    # Second ingest of EXACT SAME payload should be rejected as duplicate
    res2 = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr", 
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res2.status_code == 200, f"res2 failed: {res2.text}"
    data2 = res2.json()
    assert data2["accepted_count"] == 0
    assert data2["duplicate_count"] == 1  # Should be flagged as duplicate

@pytest.mark.asyncio
async def test_f02_entity_physical_immutability(db_session):
    # Insert a synthetic entity manually to bypass RLS/App setup needed for testing delete
    entity_id = uuid.uuid4()
    await db_session.execute(
        text("INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES (:eid, 'PERSON', 'ACTIVE')"),
        {"eid": entity_id}
    )
    
    # Try to physically delete it directly from the database session
    # This should trigger block_operational_delete
    with pytest.raises(Exception) as excinfo:
        await db_session.execute(
            text("DELETE FROM civix.entity WHERE entity_id = :eid"),
            {"eid": entity_id}
        )
    
    assert "Operational deletion of non-synthetic records is strictly forbidden." in str(excinfo.value)

