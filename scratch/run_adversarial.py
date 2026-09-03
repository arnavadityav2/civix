import asyncio
import uuid
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from civix_api.main import app
from civix_api.database import AsyncSessionLocal
from civix_api.config import settings

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "role": "INVESTIGATOR",
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

async def create_user(session, uid):
    await session.execute(
        text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:u, :auth, :uname, :uname, 'INVESTIGATOR')"),
        {"u": uid, "auth": f"auth-{uid}", "uname": str(uid)}
    )
    await session.commit()

async def run_tests():
    async with AsyncSessionLocal() as session:
        uid_A = uuid.uuid4()
        uid_B = uuid.uuid4()
        await create_user(session, uid_A)
        await create_user(session, uid_B)

        tok_A = create_token(str(uid_A))
        tok_B = create_token(str(uid_B))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            try:
                # Create Case A
                res = await ac.post("/api/v1/cases", json={"case_number": f"CA-{uuid.uuid4().hex[:6]}", "title": "Case A", "case_type": "CRIMINAL", "jurisdiction": "A"}, headers={"Authorization": f"Bearer {tok_A}"})
                case_a = res.json()["case_id"]

                # Create Case B
                res = await ac.post("/api/v1/cases", json={"case_number": f"CB-{uuid.uuid4().hex[:6]}", "title": "Case B", "case_type": "CRIMINAL", "jurisdiction": "B"}, headers={"Authorization": f"Bearer {tok_B}"})
                case_b = res.json()["case_id"]

                # Create Source
                src_id = uuid.uuid4()
                await session.execute(text("INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score) VALUES (:s, :sname, 'TELECOM', 0.9)"), {"s": src_id, "sname": f"Src-{src_id}"})
                await session.commit()

                # Ingest CDR
                caller_num = f"555{str(uuid.uuid4().int)[:7]}"
                ext_ref = f"CDR-{uuid.uuid4()}"
                res = await ac.post(f"/api/v1/cases/{case_a}/ingest/cdr", headers={"Authorization": f"Bearer {tok_A}"}, json={
                    "source_id": str(src_id),
                    "records": [{"external_reference": ext_ref, "caller_identifier": caller_num, "callee_identifier": "5559999999", "timestamp": datetime.utcnow().isoformat()}]
                })
                print(f"Ingest CDR: {res.status_code}")

                # Find entity
                db_res = await session.execute(text("SELECT entity_id FROM civix.source_identity WHERE raw_identifier = :m"), {"m": caller_num})
                row = db_res.first()
                if not row:
                    print("Could not find source_identity for CDR!")
                else:
                    entity_id = row[0]
                    # User B retrieval
                    res = await ac.get(f"/api/v1/entities/{entity_id}", headers={"Authorization": f"Bearer {tok_B}"})
                    print(f"Scenario A (Entity Retrieval by B): {res.status_code} (Expected 404)")
                    if res.status_code != 404:
                        print("  -> FAILED: User B successfully retrieved Entity from Case A!")
                    
                    # User B search
                    res = await ac.get(f"/api/v1/search?q={caller_num}", headers={"Authorization": f"Bearer {tok_B}"})
                    print(f"Scenario B (Entity Search by B): {res.status_code}, Found={res.json().get('total_count')} (Expected 0)")
                    if res.json().get('total_count', 0) > 0:
                        print("  -> FAILED: Search leaked entity from Case A to User B!")

            except Exception as e:
                print(f"Scenario A/B failed: {e}")
                await session.rollback()

            # Tombstone scenario
            try:
                t_eid = uuid.uuid4()
                await session.execute(text("SELECT set_config('civix.current_user_id', :u, true)"), {"u": str(uid_A)})
                await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES (:e, 'PERSON', 'TOMBSTONED')"), {"e": t_eid})
                await session.execute(text("INSERT INTO civix.person (entity_id, display_name, is_deceased) VALUES (:e, 'Tombstoned', false)"), {"e": t_eid})
                await session.execute(text("INSERT INTO civix.case_entity_role (case_id, entity_id, role) VALUES (:c, :e, 'SUSPECT')"), {"c": case_a, "e": t_eid})
                await session.commit()

                res = await ac.get(f"/api/v1/entities/{t_eid}", headers={"Authorization": f"Bearer {tok_A}"})
                print(f"Scenario D (Retrieve Tombstone by A): {res.status_code} (Expected 404)")
                
                res = await ac.get("/api/v1/search?q=Tombstoned", headers={"Authorization": f"Bearer {tok_A}"})
                print(f"Scenario D (Search Tombstone by A): {res.status_code}, Found={res.json().get('total_count')} (Expected 0)")
            except Exception as e:
                print(f"Scenario D failed: {e}")
                await session.rollback()

if __name__ == "__main__":
    asyncio.run(run_tests())
