import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
import jwt

from civix_api.main import app
from civix_api.database import engine, AsyncSessionLocal
from civix_api.config import settings
from sqlalchemy import text

async def run_scenario_A_B():
    print("\\n=== SCENARIO A & B: Cross-Case Isolation ===")
    async with AsyncSessionLocal() as session:
        # Create users
        uid_A = uuid.uuid4()
        uid_B = uuid.uuid4()
        case_A = uuid.uuid4()
        case_B = uuid.uuid4()
        
        await session.execute(text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:u, :auth, :uname, :uname, 'INVESTIGATOR')"), {"u": uid_A, "auth": f"auth-{uid_A}", "uname": str(uid_A)})
        await session.execute(text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:u, :auth, :uname, :uname, 'INVESTIGATOR')"), {"u": uid_B, "auth": f"auth-{uid_B}", "uname": str(uid_B)})
        
        await session.execute(text("INSERT INTO civix.investigative_case (case_id, title, status, classification, case_number) VALUES (:c, 'Case A', 'OPEN', 'UNCLASSIFIED', :cn)"), {"c": case_A, "cn": f"CA-{case_A}"})
        await session.execute(text("INSERT INTO civix.investigative_case (case_id, title, status, classification, case_number) VALUES (:c, 'Case B', 'OPEN', 'UNCLASSIFIED', :cn)"), {"c": case_B, "cn": f"CB-{case_B}"})
        
        await session.execute(text("INSERT INTO civix.case_access (case_id, user_id, access_level) VALUES (:c, :u, 'WRITE')"), {"c": case_A, "u": uid_A})
        await session.execute(text("INSERT INTO civix.case_access (case_id, user_id, access_level) VALUES (:c, :u, 'WRITE')"), {"c": case_B, "u": uid_B})
        
        source_id = uuid.uuid4()
        await session.execute(text("INSERT INTO civix.source (source_id, source_name, source_type, reliability) VALUES (:s, 'AuditSrc', 'TELCO', 'RELIABLE')"), {"s": source_id})
        await session.commit()

        token_A = jwt.encode({"sub": f"auth-{uid_A}", "role": "INVESTIGATOR", "exp": datetime.utcnow() + timedelta(hours=1)}, settings.civix_jwt_secret, algorithm="HS256")
        token_B = jwt.encode({"sub": f"auth-{uid_B}", "role": "INVESTIGATOR", "exp": datetime.utcnow() + timedelta(hours=1)}, settings.civix_jwt_secret, algorithm="HS256")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. User A ingests CDR into Case A
            ext_ref = f"CDR-AUDIT-{uuid.uuid4()}"
            caller_num = f"555000{str(uuid.uuid4().int)[:4]}"
            resp = await client.post(f"/api/v1/cases/{case_A}/ingest/cdr", headers={"Authorization": f"Bearer {token_A}"}, json={
                "source_id": str(source_id),
                "records": [{
                    "external_reference": ext_ref,
                    "caller_identifier": caller_num,
                    "callee_identifier": "5550009999",
                    "timestamp": datetime.utcnow().isoformat()
                }]
            })
            assert resp.status_code == 200, f"Ingest failed: {resp.text}"
            
            # Find the generated entity ID for the caller
            res = await session.execute(text("SELECT entity_id FROM civix.phone_number WHERE msisdn = :m"), {"m": caller_num})
            entity_id = res.scalar()
            
            # Scenario A: User B retrieves entity
            resp = await client.get(f"/api/v1/entities/{entity_id}", headers={"Authorization": f"Bearer {token_B}"})
            print(f"Scenario A (Retrieve as User B): Status {resp.status_code} (Expected 404)")
            
            # Scenario B: User B searches entity
            resp = await client.post(f"/api/v1/search", headers={"Authorization": f"Bearer {token_B}"}, json={"query": caller_num})
            data = resp.json()
            print(f"Scenario B (Search as User B): Found {data['total_count']} results (Expected 0)")

async def run_scenario_D():
    print("\\n=== SCENARIO D: Tombstone Attack ===")
    async with AsyncSessionLocal() as session:
        # Create user & case
        uid = uuid.uuid4()
        case_id = uuid.uuid4()
        await session.execute(text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:u, :auth, :uname, :uname, 'INVESTIGATOR')"), {"u": uid, "auth": f"auth-{uid}", "uname": str(uid)})
        await session.execute(text("INSERT INTO civix.investigative_case (case_id, title, status, classification, case_number) VALUES (:c, 'Case D', 'OPEN', 'UNCLASSIFIED', :cn)"), {"c": case_id, "cn": f"CD-{case_id}"})
        await session.execute(text("INSERT INTO civix.case_access (case_id, user_id, access_level) VALUES (:c, :u, 'WRITE')"), {"c": case_id, "u": uid})
        await session.commit()
        
        token = jwt.encode({"sub": f"auth-{uid}", "role": "INVESTIGATOR", "exp": datetime.utcnow() + timedelta(hours=1)}, settings.civix_jwt_secret, algorithm="HS256")
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create Person directly in DB since there's no POST /entities yet
            entity_id = uuid.uuid4()
            await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type) VALUES (:e, 'PERSON')"), {"e": entity_id})
            await session.execute(text("INSERT INTO civix.person (entity_id, full_name, is_tombstoned) VALUES (:e, 'Tombstoned Bob', true)"), {"e": entity_id})
            await session.execute(text("INSERT INTO civix.case_entity_role (case_id, entity_id, role) VALUES (:c, :e, 'SUBJECT')"), {"c": case_id, "e": entity_id})
            await session.commit()
            
            # 1. Retrieve
            resp = await client.get(f"/api/v1/entities/{entity_id}", headers={"Authorization": f"Bearer {token}"})
            print(f"Scenario D (Retrieve Tombstoned): Status {resp.status_code} (Expected 404)")
            
            # 2. Search
            resp = await client.post(f"/api/v1/search", headers={"Authorization": f"Bearer {token}"}, json={"query": "Tombstoned Bob"})
            data = resp.json()
            print(f"Scenario D (Search Tombstoned): Found {data['total_count']} results (Expected 0)")

async def main():
    await run_scenario_A_B()
    await run_scenario_D()

if __name__ == "__main__":
    asyncio.run(main())
