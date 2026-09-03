import uuid

new_test = '''
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
'''
with open('tests/api/test_ingest.py', 'a') as f:
    f.write(new_test)
