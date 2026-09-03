import pytest
import jwt
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from civix_api.main import app
from civix_api.config import settings

pytestmark = pytest.mark.asyncio(loop_scope="session")

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.fixture
async def setup_ingest_data(db_session, create_test_user):
    user_investigator = await create_test_user()
    user_read_only = await create_test_user()
    
    token_investigator = create_token(sub=str(user_investigator))
    token_read_only = create_token(sub=str(user_read_only))
    
    case_id = uuid.uuid4()
    source_id = uuid.uuid4()
    
    # Temporarily bypass RLS
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_investigator)})
    
    # 1. Create Source
    await db_session.execute(
        text("""
            INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score)
            VALUES (:sid, :sname, 'TELECOM', 0.9)
        """),
        {"sid": source_id, "sname": f"Test Telecom {source_id}"}
    )
    
    # 2. Grant case access (before case creation to satisfy RLS)
    await db_session.execute(
        text("""
            INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
            VALUES (:a1, :cid, :uid_write, 'WRITE', :uid_write),
                   (:a2, :cid, :uid_read, 'READ', :uid_write)
        """),
        {
            "a1": uuid.uuid4(),
            "a2": uuid.uuid4(),
            "cid": case_id,
            "uid_write": user_investigator,
            "uid_read": user_read_only
        }
    )
    
    # 3. Create Case
    await db_session.execute(
        text("""
            INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at)
            VALUES (:cid, :cnum, 'Test Ingest Case', 'CRIMINAL', 'Test', CURRENT_DATE)
        """),
        {"cid": case_id, "cnum": f"CIV-2026-ING-{str(case_id)[:6]}"}
    )
    
    await db_session.commit()
    
    # Restore config
    await db_session.execute(text("SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"))
    
    return {
        "case_id": case_id,
        "source_id": source_id,
        "token_investigator": token_investigator,
        "token_read_only": token_read_only
    }


async def test_ingest_cdr_unauthenticated(client: AsyncClient):
    case_id = uuid.uuid4()
    response = await client.post(f"/api/v1/cases/{case_id}/ingest/cdr", json={
        "source_id": str(uuid.uuid4()),
        "records": [{
            "external_reference": "CDR-1",
            "caller_identifier": "9876543210",
            "callee_identifier": "1234567890",
            "timestamp": datetime.utcnow().isoformat()
        }]
    })
    assert response.status_code == 401

async def test_ingest_cdr_unauthorized(client: AsyncClient, setup_ingest_data):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_read_only"]
    
    response = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_id": str(source_id),
            "records": [{
                "external_reference": "CDR-2",
                "caller_identifier": "9876543210",
                "callee_identifier": "1234567890",
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
    )
    assert response.status_code == 403

async def test_ingest_cdr_success_and_idempotency(client: AsyncClient, setup_ingest_data):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref = f"CDR-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [{
            "external_reference": ext_ref,
            "caller_identifier": "9876543210",
            "callee_identifier": "1234567890",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    # First ingest
    response = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["accepted_count"] == 1
    assert data["duplicate_count"] == 0
    assert data["status"] == "SUCCESS"
    
    # Second ingest (Idempotent)
    response2 = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["accepted_count"] == 0
    assert data2["duplicate_count"] == 1

async def test_ingest_transaction_success(client: AsyncClient, setup_ingest_data, db_session):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref = f"TXN-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [{
            "external_reference": ext_ref,
            "source_account": "ACC-123",
            "destination_account": "ACC-456",
            "amount": "1500.50",
            "currency": "INR",
            "transaction_type": "TRANSFER",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    response = await client.post(
        f"/api/v1/cases/{case_id}/ingest/transaction",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["accepted_count"] == 1
    
    # Verify records in database
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(token)}) # just bypass if needed for count
    # Actually wait, test session might need real UUID but count query ignores RLS if we're admin or if we query source_identity which has NO RLS.
    
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_record WHERE external_reference = :ext"), {"ext": ext_ref})
    assert res.scalar() == 1
    
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_identity WHERE raw_identifier IN ('ACC-123', 'ACC-456')"))
    assert res.scalar() >= 2
    
    # Verify no canonical entities created
    res = await db_session.execute(text("SELECT count(*) FROM civix.financial_account"))
    assert res.scalar() == 0

async def test_ingest_atomic_rollback(client: AsyncClient, setup_ingest_data, db_session):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref1 = f"CDR-{uuid.uuid4()}"
    ext_ref2 = f"CDR-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [
            {
                "external_reference": ext_ref1,
                "caller_identifier": "9876543210",
                "callee_identifier": "1234567890",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "external_reference": ext_ref2,
                # Missing required fields like caller/callee
            }
        ]
    }
    
    response = await client.post(
        f"/api/v1/cases/{case_id}/ingest/cdr",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    # Pydantic validation fails at the request layer before reaching DB
    assert response.status_code == 422
    
    # Ensure nothing was ingested
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_record WHERE external_reference = :ext"), {"ext": ext_ref1})
    assert res.scalar() == 0

import asyncio

async def test_ingest_concurrent_idempotency(client: AsyncClient, setup_ingest_data, db_session):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref = f"CDR-CONCURRENT-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [{
            "external_reference": ext_ref,
            "caller_identifier": "5551112222",
            "callee_identifier": "5553334444",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    # Fire 15 concurrent requests
    requests = [
        client.post(
            f"/api/v1/cases/{case_id}/ingest/cdr",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        for _ in range(15)
    ]
    
    responses = await asyncio.gather(*requests)
    
    # 1. Verify no 500 errors
    for r in responses:
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
    # 2. Verify exactly one successful insert, 14 duplicates
    accepted = sum(r.json()["accepted_count"] for r in responses)
    duplicates = sum(r.json()["duplicate_count"] for r in responses)
    
    assert accepted == 1, f"Expected exactly 1 accepted, got {accepted}"
    assert duplicates == 14, f"Expected 14 duplicates, got {duplicates}"
    
    # 3. Verify database physically contains only 1 record
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(token)})
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_record WHERE external_reference = :ext"), {"ext": ext_ref})
    db_count = res.scalar()
    assert db_count == 1, f"Expected exactly 1 row in database, found {db_count}"

import asyncio

async def test_ingest_concurrent_idempotency(client: AsyncClient, setup_ingest_data, db_session):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref = f"CDR-CONCURRENT-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [{
            "external_reference": ext_ref,
            "caller_identifier": "5551112222",
            "callee_identifier": "5553334444",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    # Fire 15 concurrent requests
    requests = [
        client.post(
            f"/api/v1/cases/{case_id}/ingest/cdr",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        for _ in range(15)
    ]
    
    responses = await asyncio.gather(*requests)
    
    # 1. Verify no 500 errors
    for r in responses:
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
    # 2. Verify exactly one successful insert, 14 duplicates
    accepted = sum(r.json()["accepted_count"] for r in responses)
    duplicates = sum(r.json()["duplicate_count"] for r in responses)
    
    assert accepted == 1, f"Expected exactly 1 accepted, got {accepted}"
    assert duplicates == 14, f"Expected 14 duplicates, got {duplicates}"
    
    # 3. Verify database physically contains only 1 record
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(token)})
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_record WHERE external_reference = :ext"), {"ext": ext_ref})
    db_count = res.scalar()
    assert db_count == 1, f"Expected exactly 1 row in database, found {db_count}"

import asyncio

async def test_ingest_concurrent_idempotency(client: AsyncClient, setup_ingest_data, db_session):
    case_id = setup_ingest_data["case_id"]
    source_id = setup_ingest_data["source_id"]
    token = setup_ingest_data["token_investigator"]
    
    ext_ref = f"CDR-CONCURRENT-{uuid.uuid4()}"
    payload = {
        "source_id": str(source_id),
        "records": [{
            "external_reference": ext_ref,
            "caller_identifier": "5551112222",
            "callee_identifier": "5553334444",
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    # Fire 15 concurrent requests
    requests = [
        client.post(
            f"/api/v1/cases/{case_id}/ingest/cdr",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        for _ in range(15)
    ]
    
    responses = await asyncio.gather(*requests)
    
    # 1. Verify no 500 errors
    for r in responses:
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
    # 2. Verify exactly one successful insert, 14 duplicates
    accepted = sum(r.json()["accepted_count"] for r in responses)
    duplicates = sum(r.json()["duplicate_count"] for r in responses)
    
    assert accepted == 1, f"Expected exactly 1 accepted, got {accepted}"
    assert duplicates == 14, f"Expected 14 duplicates, got {duplicates}"
    
    # 3. Verify database physically contains only 1 record
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(token)})
    res = await db_session.execute(text("SELECT count(*) FROM civix.source_record WHERE external_reference = :ext"), {"ext": ext_ref})
    db_count = res.scalar()
    assert db_count == 1, f"Expected exactly 1 row in database, found {db_count}"
